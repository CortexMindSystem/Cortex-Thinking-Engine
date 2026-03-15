import random
import string


def generate_coupon():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


coupons = [generate_coupon() for _ in range(50)]

with open("coupons.txt", "w") as f:
    f.write("\n".join(coupons))

print("Generated 50 coupons.")
