"""
Линейная регрессия методом наименьших квадратов (МНК).

Используется для прогнозирования балла экзамена
по среднему баллу за занятия.
"""


def linear_regression(x_vals, y_vals):
    """
    Простая линейная регрессия: y = slope * x + intercept.

    Параметры:
        x_vals — список значений признака (средний балл за занятия)
        y_vals — список значений отклика (балл экзамена)

    Возвращает:
        (slope, intercept, r_squared)  или  (None, None, None) если данных < 2.
    """
    n = len(x_vals)
    if n < 2:
        return None, None, None

    sum_x  = sum(x_vals)
    sum_y  = sum(y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    sum_x2 = sum(x * x for x in x_vals)

    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return None, None, None

    slope     = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    ss_res = sum((y - (slope * x + intercept)) ** 2
                 for x, y in zip(x_vals, y_vals))
    r_sq = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0

    return slope, intercept, r_sq


def predict(slope, intercept, x):
    """
    Предсказать значение y по значению x.
    Результат ограничивается диапазоном [0, 100].
    """
    if slope is None or intercept is None:
        return None
    return max(0.0, min(100.0, slope * x + intercept))
