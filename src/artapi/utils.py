from fractions import Fraction

def format_inches(value):
    # Convert the value to a fraction with denominator 4 (quarters)
    fraction = Fraction(value).limit_denominator(4)
    
    # Get the integer and fractional parts
    integer_part = fraction.numerator // fraction.denominator
    fractional_part = fraction.numerator % fraction.denominator
    
    if fractional_part == 0:
        return f'{integer_part}<span class="inch-mark">"</span>'
    else:
        # Return as a real fraction with a horizontal line
        return (
            f'{integer_part} '
            f'<span class="fraction">'
            f'<span class="numerator">{fractional_part}</span>'
            f'<span class="fraction-bar"></span>'
            f'<span class="denominator">{fraction.denominator}</span>'
            f'</span><span class="inch-mark">"</span>'
        )