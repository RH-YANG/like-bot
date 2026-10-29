import secrets
import string
from pathlib import Path



# ========== 루트 .env 초기 생성 (기존 .env는 덮어쓰지 않는다) ==========



ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_EXAMPLE_PATH = ROOT_DIR / '.env.example'
ENV_PATH = ROOT_DIR / '.env'
SECRET_LENGTH = {
    'DB_PWD': 24,
}



def generate_secret(length):
    alphabet = string.ascii_letters + string.digits
    secret = ''.join(secrets.choice(alphabet) for _ in range(length))

    return secret



def build_env_text(example_text):
    line_list = []
    for line in example_text.splitlines():
        key, separator, value = line.partition('=')
        if separator and key in SECRET_LENGTH and value == '':
            line = f'{key}={generate_secret(SECRET_LENGTH[key])}'
        line_list.append(line)

    env_text = '\n'.join(line_list) + '\n'

    return env_text



def main():
    if ENV_PATH.exists():
        print(f'이미 존재합니다: {ENV_PATH}')
        return

    example_text = ENV_EXAMPLE_PATH.read_text(encoding='utf-8')
    env_text = build_env_text(example_text)
    ENV_PATH.write_text(env_text, encoding='utf-8', newline='\n')
    print(f'생성했습니다: {ENV_PATH}')



if __name__ == '__main__':
    main()
