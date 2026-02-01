from django.shortcuts import render, get_object_or_404
from django.db import transaction
from articles.models import Article
from explanations.models import ArticleExplanation
from .utils import GeminiFinancialTutor

def explanation_detail(request, article_id):
    # 1. 기사 객체 가져오기
    article = get_object_or_404(Article, pk=article_id)
    
    # 2. 사용자 정보 설정 (테스트 및 실제 환경 통합)
    if request.user.is_authenticated:
        # [로그인 유저]
        user_interests = ["부동산", "주식"]  # 임시 관심사
            
        # [TEST] 관리자는 레벨 5로 설정
        if request.user.is_superuser:
            print(f"[Test] 관리자('{request.user}') 접속: 레벨 5(최고 레벨)로 간주")
            user_level = 5
        else:
            user_level = request.user.level
    else:
        # [비로그인 유저 - TEST MODE]
        print("[Test] 비로그인 유저 접속: 관심사(부동산, 주식), 레벨(5)로 설정됨")
        user_interests = ["부동산", "주식"]
        user_level = 5

    # 3. DB에 이미 생성된 해설이 있는지 확인
    explanations = ArticleExplanation.objects.filter(article=article).order_by('level')
    
    # 4. 해설이 없다면? -> AI 분석 시작 (최초 1회)
    if not explanations.exists():
        # 카테고리명 안전하게 가져오기
        try:
            category_name = article.category.name if article.category else "경제"
        except AttributeError:
            category_name = "경제"

        print(f"'{article.title}' AI 분석 시작 (카테고리: {category_name})...")
        
        # AI 호출
        tutor = GeminiFinancialTutor()
        analysis_data = tutor.generate_analysis(
            text=article.content,
            category=category_name,
            interests=user_interests
        )

        # DB 저장 (트랜잭션으로 안전하게)
        if analysis_data:
            with transaction.atomic():
                new_explanations = []
                for data in analysis_data:
                    print(f"🔍 [저장 전 데이터] Level {data.get('level')}: {list(data.keys())}")
                    
                    # ✅ AI 응답 키에 맞게 수정
                    level = data.get('level', 1)
                    
                    # storytelling -> article_explanation
                    content_text = data.get('storytelling', '내용 없음')
                    
                    # terms 배열을 텍스트로 변환 -> term_explanation
                    terms_list = data.get('terms', [])
                    if isinstance(terms_list, list) and terms_list:
                        # [{"term": "용어1", "explanation": "설명1"}, ...] 형식
                        term_text = "\n\n".join([
                            f"📌 {item.get('term', '용어')}\n{item.get('explanation', '설명 없음')}"
                            for item in terms_list
                        ])
                    else:
                        term_text = "용어 설명 없음"
                    
                    # advice -> prediction
                    pred_text = data.get('advice', '전망 없음')

                    expl = ArticleExplanation.objects.create(
                        article=article,
                        level=level,
                        article_explanation=content_text,
                        term_explanation=term_text,
                        prediction=pred_text
                    )
                    new_explanations.append(expl)
                    print(f"✅ Level {level} 저장 완료")
                
                explanations = new_explanations
                print("✅ AI 분석 완료 및 DB 저장 성공")
        else:
            print("⚠️ AI 분석 실패 (데이터 반환 없음)")

    # 5. 템플릿에 전달
    context = {
        'article': article,
        'explanations': explanations,
        'user_level': user_level,
    }
    
    return render(request, 'ai_explain.html', context)