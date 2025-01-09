from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional, List, Dict
from datetime import datetime
import jwt
import os
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TokenCache:
    """
    Caché local para almacenar información de autenticación válida recibida a través de eventos
    """

    def __init__(self):
        self._cache: Dict[str, dict] = {}
        self._users_cache: List[dict] = []
        self.jwt_secret = os.getenv("JWT_SECRET", "51830ee1-b1f4-4e3b-a8f0-f6747bc95391")

    def get_token_info(self, user_id: str) -> Optional[dict]:
        """
        Obtiene la información del token para un usuario específico.
        Este método es un alias de get_user_session para mantener consistencia
        con la nomenclatura del servicio de asignación de cursos.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[dict]: Información del token/sesión del usuario o None si no existe
        """
        logging.info(f"Token para el usuario {user_id}")
        session_info = self.get_user_session(user_id)
        logging.info(f"session_info: {session_info}")
        if session_info:
            return {
                "userId": user_id,
                "username": session_info.get('username'),
                "roles": session_info.get('roles', []),
                "courseIds": session_info.get('courseIds', []),
                "email": session_info.get('email')
            }
        return None

    def update_users_list(self, users: List[dict]):
        """Actualiza la lista completa de usuarios en caché"""
        self._users_cache = users

    def get_all_users(self) -> List[dict]:
        """Retorna la lista completa de usuarios"""
        return self._users_cache

    def add_user_session(self, user_id: str, session_info: dict):
        """
        Almacena la información de la sesión del usuario, incluyendo roles y permisos
        """
        session_info['timestamp'] = datetime.now()
        self._cache[user_id] = session_info

    def get_user_session(self, user_id: str) -> Optional[dict]:
        """
        Recupera la información de sesión del usuario desde la caché
        """
        logging.info(f"Obteniendo sesión de usuario {user_id} desde la caché")
        logging.info(f"Cache: {self._cache}")
        return self._cache.get(user_id)

    def invalidate_session(self, user_id: str):
        """
        Invalida la sesión de un usuario
        """
        self._cache.pop(user_id, None)

    def validate_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload.get('userId')

            # Verificar si tenemos información de sesión para este usuario
            session_info = self.get_user_session(user_id)

            # Si no hay información en caché, crear y almacenar nueva información
            if not session_info:
                session_info = {
                    "username": payload.get('sub'),
                    "roles": payload.get('roles', []),
                    "courseIds": payload.get('courseIds', []),
                    "email": None
                }
                # Almacenar en caché
                self.add_user_session(user_id, session_info)

            return {
                "userId": user_id,
                **session_info
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")


class EventBasedAuthHandler:
    def __init__(self):
        self.token_cache = TokenCache()

    def handle_auth_event(self, event: dict):
        event_type = event.get('type')
        user_id = event.get('userId')
        logging.info(f"Manejando evento de autenticación: {event_type} para usuario {user_id}")

        if event_type == 'USERS_LIST_UPDATED':
            # Actualizar la lista completa de usuarios
            users = event.get('users', [])
            self.token_cache.update_users_list(users)
            logging.info(f"Lista de usuarios actualizada con {len(users)} usuarios")

        # Mapear tipos de eventos
        elif event_type in ['LOGIN', 'REGISTER']:
            # Almacenar información de la sesión
            self.token_cache.add_user_session(user_id, {
                'username': event.get('username'),
                'roles': event.get('roles', []),
                'courseIds': event.get('courseIds', []),
                'email': event.get('email')
            })
            logging.info(f"Sesión almacenada para usuario {user_id}")
        elif event_type == 'ROLE_UPDATE':
            session_info = self.token_cache.get_user_session(user_id)
            if session_info:
                session_info.update({
                    'roles': event.get('roles', session_info.get('roles', [])),
                })
                self.token_cache.add_user_session(user_id, session_info)
                logging.info(f"Roles actualizados para usuario {user_id}")


class JWTBearerHandler(HTTPBearer):
    def __init__(self, auth_handler: EventBasedAuthHandler, required_roles: Optional[List[str]] = None):
        super().__init__(auto_error=True)
        self.auth_handler = auth_handler
        self.required_roles = required_roles

    async def __call__(self, request: Request):
        credentials = await super().__call__(request)

        # Validar token y obtener información de sesión
        session_info = self.auth_handler.token_cache.validate_token(credentials.credentials)

        # Verificar roles si son requeridos
        if self.required_roles:
            user_roles = session_info.get('roles', [])
            if not any(role in user_roles for role in self.required_roles):
                raise HTTPException(
                    status_code=403,
                    detail="Permisos insuficientes"
                )

        # Almacenar información en el request state
        request.state.user = session_info
        return session_info


# Inicializar el manejador de eventos
auth_handler = EventBasedAuthHandler()


# Funciones de ayuda para diferentes niveles de acceso
def require_auth():
    return JWTBearerHandler(auth_handler)


def require_admin():
    return JWTBearerHandler(auth_handler, required_roles=["ADMIN"])


def require_instructor():
    return JWTBearerHandler(auth_handler, required_roles=["INSTRUCTOR"])


def verify_course_access(course_id: str, request: Request):
    """
    Verifica el acceso a un curso específico
    """
    user = request.state.user
    if course_id not in user.get('courseIds', []):
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a este curso"
        )
    return True
