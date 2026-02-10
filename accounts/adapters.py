from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    
    def pre_social_login(self, request, sociallogin):
        """
        소셜 로그인 직전에 호출됨.
        이미 가입된 이메일이 있다면 해당 계정에 소셜 계정을 연결함.
        """
        # 1. 소셜 로그인 시도 중인 유저의 이메일 가져오기
        user = sociallogin.user
        if not user.email:
            return

        User = get_user_model()
        
        try:
            # 2. DB에 같은 이메일을 가진 유저가 있는지 확인
            existing_user = User.objects.get(email=user.email)
            
            # 3. 이미 존재하는 유저라면, 현재 소셜 로그인을 이 유저 계정에 연결
            if not sociallogin.is_existing:
                sociallogin.connect(request, existing_user)
                
        except User.DoesNotExist:
            # 신규 유저라면 아무 작업 없이 통과 (일반적인 가입 절차 진행)
            pass

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        # 네이버/카카오 등에서 준 이메일
        email = data.get('email')
        if email:
            # 이메일 앞자리를 username으로 설정 (이미 위에서 연결된 유저라면 이 과정은 무시됨)
            auto_name = email.split('@')[0]
            if not user.username:
                user.username = data.get('username', auto_name)
            
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        # 소셜 가입 시 별도의 추가 폼 페이지를 띄우지 않고 바로 가입 완료
        return True