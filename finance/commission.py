commission_rate = 0.02

def calculate_final_amount(amount: int) -> int:
    """
    Расчет окончательной суммы с учетом комиссии
    """
    commission = calculate_commission(amount)
    return max(amount - commission, 0)

def calculate_commission(amount: int) -> int:
    """
    Расчет комиссии
    """
    if amount < 100:
        return 2
    return int(amount * commission_rate)
