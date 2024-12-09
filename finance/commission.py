def calculate_final_amount(amount: int) -> int:
    """
    Расчет окончательной суммы с учетом комиссии
    """
    if amount < 100:
        return max(amount - 2, 0)
    return int(amount * 0.98)
