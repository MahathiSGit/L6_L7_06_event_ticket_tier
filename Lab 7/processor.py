def decode_promo_voucher(voucher_code):
    if not isinstance(voucher_code, str):
        return "Invalid voucher: input must be text"

    code = voucher_code.strip()

    parts = code.split('-')

    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return "Invalid voucher: expected FORMAT like EARLY-20"

    prefix, pct_str = parts

    try:
        percentage = int(pct_str)
    except ValueError:
        return "Invalid voucher: percentage must be a number"

    if percentage <= 0 or percentage > 100:
        return "Invalid voucher: percentage must be between 1 and 100"

    return f"Valid {prefix.upper()}: {percentage}% OFF"


def calculate_seat_tier_price(tier_spec):
    if not isinstance(tier_spec, str):
        return "Invalid tier specification"

    parts = tier_spec.split('@')

    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        return "Invalid tier specification: expected VIP@4"

    tier = parts[0].strip().upper()

    try:
        row = int(parts[1])
    except ValueError:
        return "Invalid row number"

    tier_rates = {
        "VIP": 150.0,
        "PREMIUM": 90.0,
        "GENERAL": 45.0
    }

    if tier not in tier_rates:
        return "Invalid seat tier"

    if row < 1:
        return "Invalid row number"

    base = tier_rates[tier]
    return base + (row * 2.0)


def parse_attendee_badge(badge_csv):
    if not isinstance(badge_csv, str):
        return "Invalid badge: input must be text"

    tokens = badge_csv.split(',')

    if len(tokens) != 3:
        return "Invalid badge: expected Name,Age,Seat"

    name = tokens[0].strip()
    seat = tokens[2].strip()

    if not name or not seat:
        return "Invalid badge: name and seat cannot be empty"

    try:
        age = int(tokens[1].strip())
    except ValueError:
        return "Invalid badge: age must be a number"

    if age < 0:
        return "Invalid badge: age cannot be negative"

    category = "Child" if age < 18 else "Adult"

    return f"{name} [{category}] - Seat {seat}"


def main():
    print("==== Running decode_promo_voucher ====")
    v_input = input("Enter voucher (e.g. EARLY-20): ")
    print("Voucher:", decode_promo_voucher(v_input))

    print("\n==== Running calculate_seat_tier_price ====")
    t_input = input("Enter tier spec (e.g. VIP@4): ")
    print("Seat Price: $", calculate_seat_tier_price(t_input))

    print("\n==== Running parse_attendee_badge ====")
    b_input = input("Enter badge CSV (Name,Age,Seat): ")
    print("Badge:", parse_attendee_badge(b_input))


if __name__ == "__main__":
    main()