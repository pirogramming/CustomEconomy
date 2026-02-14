import subprocess
import sys

def run_script(script_path):
    print(f"--- 실행 중: {script_path} ---")
    try:
        # 현재 파이썬 실행기로 스크립트 실행
        result = subprocess.run([sys.executable, script_path], check=True)
        print(f"✅ 완료: {script_path}\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ 실패: {script_path} (에러 코드: {e.returncode})")
        sys.exit(1)

if __name__ == "__main__":
    # 실행할 스크립트 순서
    scripts = [
        "scripts/setup_meta.py",
        "scripts/load_to_db.py",
        "scripts/b_build_quiz.py"
    ]

    print("🚀 서비스 초기 데이터 로드를 시작합니다.")
    
    for s in scripts:
        run_script(s)

    print("✨ 모든 초기 데이터 세팅이 성공적으로 끝났습니다!")