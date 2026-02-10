# accounts/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        # 네이버에서 준 이메일
        email = data.get('email')
        if email:
            auto_name = email.split('@')[0]
            # fill username from email prefix if provider didn't supply one
            user.username = data.get('username', auto_name)
            
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        return True # 창 띄우지 말고 그냥 가입 진행해라!