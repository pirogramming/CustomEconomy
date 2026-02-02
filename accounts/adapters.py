# accounts/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        # 네이버에서 준 이메일
        email = data.get('email')
        if email:
            auto_name = email.split('@')[0]
            # 1. 시현님 모델의 ID 필드인 nickname 채우기
            user.nickname = auto_name
            # 2. 필수 필드인 name 채우기 (네이버 이름 없으면 이메일 앞부분)
            user.name = data.get('name', auto_name)
            # 3. 나머지 필수 필드 기본값
            user.age = 20
            user.job = "unknown"
            
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        return True # 창 띄우지 말고 그냥 가입 진행해라!