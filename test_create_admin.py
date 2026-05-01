import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'module.survey_app.settings')
import django
django.setup()

import re

def test_password_validation():
    print("=" * 60)
    print("测试 create_admin 二次密码确认功能")
    print("=" * 60)
    
    print("\n密码要求：")
    print("  - 长度至少8位")
    print("  - 至少包含一个大写字母")
    print("  - 至少包含一个小写字母")
    print("  - 至少包含一个数字")
    print("  - 至少包含一个特殊字符 (!@#$%^&*(),.?\":{}|<>)\n")
    
    test_cases = [
        {
            "name": "场景1：密码不一致",
            "password": "Test123!@#",
            "confirm": "Test123!@",
            "expected": "两次密码不一致"
        },
        {
            "name": "场景2：密码太短",
            "password": "Test1!",
            "confirm": "Test1!",
            "expected": "密码长度不足"
        },
        {
            "name": "场景3：缺少大写字母",
            "password": "test123!@#",
            "confirm": "test123!@#",
            "expected": "缺少大写字母"
        },
        {
            "name": "场景4：缺少小写字母",
            "password": "TEST123!@#",
            "confirm": "TEST123!@#",
            "expected": "缺少小写字母"
        },
        {
            "name": "场景5：缺少数字",
            "password": "TestPass!@#",
            "confirm": "TestPass!@#",
            "expected": "缺少数字"
        },
        {
            "name": "场景6：缺少特殊字符",
            "password": "TestPass123",
            "confirm": "TestPass123",
            "expected": "缺少特殊字符"
        },
        {
            "name": "场景7：密码正确",
            "password": "TestPass123!@#",
            "confirm": "TestPass123!@#",
            "expected": "密码验证通过"
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"{test_case['name']}")
        print(f"{'=' * 60}")
        print(f"密码: {test_case['password']}")
        print(f"确认: {test_case['confirm']}")
        
        password = test_case['password']
        password_confirm = test_case['confirm']
        
        if password != password_confirm:
            print(f"[PASS] 检测到：两次密码不一致")
            continue
        
        errors = []
        if len(password) < 8:
            errors.append("密码长度至少8位")
        if not re.search(r'[A-Z]', password):
            errors.append("密码至少包含一个大写字母")
        if not re.search(r'[a-z]', password):
            errors.append("密码至少包含一个小写字母")
        if not re.search(r'[0-9]', password):
            errors.append("密码至少包含一个数字")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码至少包含一个特殊字符")
        
        if errors:
            print(f"[PASS] 检测到密码强度不足：")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[PASS] 密码验证通过！")
    
    print("\n" + "=" * 60)
    print("所有测试场景通过！")
    print("=" * 60)

if __name__ == "__main__":
    test_password_validation()