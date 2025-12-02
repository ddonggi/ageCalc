from controllers.age_controller import AgeController

def test_lunar():
    controller = AgeController()
    print("Testing 1990-01-01 (Lunar)...")
    result = controller.calculate_age_from_string('1990-01-01', 'lunar')
    print(result)

if __name__ == "__main__":
    test_lunar()
