from config import ADMIN_ID

def is_user_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором с определенным user_id.
    
    :param user_id: ID пользователя для проверки.
    :return: True, если ID равен 779294895, иначе False.
    """
    return str(user_id) == ADMIN_ID
