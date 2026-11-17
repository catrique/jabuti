# O único destino permitido é "$DEPLOY_ROOT/$APP". DEPLOY_ROOT vem de uma
# GitHub Actions Variable e é tratado como entrada não confiável.
if [[ ! "$APP" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then
  echo "APP inválido: $APP" >&2
  exit 1
fi

if [ -z "${DEPLOY_ROOT:-}" ]; then
  echo "GitHub Actions Variable DEPLOY_ROOT não configurada." >&2
  exit 1
fi

if [[ "$DEPLOY_ROOT" == *$'\n'* || "$DEPLOY_ROOT" == *$'\r'* ]]; then
  echo "DEPLOY_ROOT inválido: contém quebra de linha." >&2
  exit 1
fi

case "$DEPLOY_ROOT" in
  /*) ;;
  *)
    echo "DEPLOY_ROOT deve ser um caminho absoluto." >&2
    exit 1
    ;;
esac

case "$DEPLOY_ROOT/" in
  */./*|*/../*)
    echo "DEPLOY_ROOT não pode conter os segmentos '.' ou '..'." >&2
    exit 1
    ;;
esac

if [ -L "$DEPLOY_ROOT" ]; then
  echo "DEPLOY_ROOT não pode ser um link simbólico." >&2
  exit 1
fi

if [ ! -d "$DEPLOY_ROOT" ]; then
  echo "DEPLOY_ROOT não existe no servidor ou não é um diretório." >&2
  exit 1
fi

deploy_base=$(realpath -e -- "$DEPLOY_ROOT")
home_directory=$(realpath -m -- "${HOME:-/}")

if [ "$deploy_base" = / ] || [ "$deploy_base" = "$home_directory" ] ||
  [[ "$deploy_base" == *$'\n'* ]]; then
  echo "DEPLOY_ROOT não pode ser a raiz do sistema nem o diretório home." >&2
  exit 1
fi

deploy_target="$deploy_base/$APP"

if [ -L "$deploy_target" ]; then
  echo "Destino simbólico proibido: $APP" >&2
  exit 1
fi

if [ -e "$deploy_target" ] && [ ! -d "$deploy_target" ]; then
  echo "O destino de $APP existe e não é um diretório." >&2
  exit 1
fi

if [ "$(dirname -- "$(realpath -m -- "$deploy_target")")" != "$deploy_base" ]; then
  echo "Destino fora de DEPLOY_ROOT: $APP" >&2
  exit 1
fi

{
  printf 'DEPLOY_BASE=%s\n' "$deploy_base"
  printf 'DEPLOY_TARGET=%s\n' "$deploy_target"
} >> "$GITHUB_ENV"
