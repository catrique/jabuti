name: %%WORKFLOW_NAME%%

on:
  push:
    branches: [main]
%%PUSH_FILTER%%
  workflow_dispatch:

permissions:
  contents: read

# APP, SRC, TIPO e OUT pertencem ao projeto. DEPLOY_ROOT e DEPLOY_USER
# pertencem ao servidor e vêm de GitHub Actions Variables.
env:
  APP: '%%APP%%'
  SRC: '%%SRC%%'
  TIPO: '%%TIPO%%'
%%OUT_ENV%%
  DEPLOY_ROOT: ${{ vars.DEPLOY_ROOT }}
  DEPLOY_USER: ${{ vars.DEPLOY_USER }}

concurrency:
  group: deploy-${{ github.workflow_ref }}
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: [self-hosted, Linux, X64]

    defaults:
      run:
        shell: bash

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Validar configuração
        run: |
          case "$TIPO" in
            python) required=requirements.txt ;;
            node|react|angular|next) required=package.json ;;
            static) required=index.html ;;
            *)
              echo "TIPO inválido: $TIPO" >&2
              exit 1
              ;;
          esac

          [ -d "$SRC" ] || {
            echo "SRC não existe: $SRC" >&2
            exit 1
          }

          workspace=$(realpath -e -- "$GITHUB_WORKSPACE")
          project=$(realpath -e -- "$SRC")

          case "$project" in
            "$workspace"|"$workspace"/*) ;;
            *)
              echo "SRC fora do repositório: $SRC" >&2
              exit 1
              ;;
          esac

          [ -f "$SRC/$required" ] || {
            echo "Arquivo ausente: $SRC/$required" >&2
            exit 1
          }

          if [ "$TIPO" = react ] || [ "$TIPO" = angular ]; then
            [ -f "$SRC/package-lock.json" ] || {
              echo "Arquivo ausente: $SRC/package-lock.json" >&2
              exit 1
            }
          fi

          if [ "$TIPO" = angular ] && [ -z "${OUT:-}" ]; then
            echo "Configure OUT com a pasta gerada pelo Angular." >&2
            exit 1
          fi

          if [ -n "${DEPLOY_USER:-}" ] &&
            [[ ! "$DEPLOY_USER" =~ ^[A-Za-z_][A-Za-z0-9_-]{0,31}$ ]]; then
            echo "GitHub Actions Variable DEPLOY_USER inválida." >&2
            exit 1
          fi

%%RESOLVE_TARGET%%

          echo "Destino de deploy validado."

      - name: Configurar Node.js
        if: env.TIPO == 'angular'
        uses: actions/setup-node@v4
        with:
          node-version: '22.22.3'
          cache: npm
          cache-dependency-path: '%%LOCKFILE%%'

      - name: Instalar dependências
        if: env.TIPO == 'react' || env.TIPO == 'angular'
        working-directory: ./${{ env.SRC }}
        run: npm ci

      - name: Gerar build
        if: env.TIPO == 'react' || env.TIPO == 'angular'
        working-directory: ./${{ env.SRC }}
        run: npm run build

      - name: Publicar aplicação
        if: env.TIPO != 'next'
        run: |
          case "$TIPO" in
            react) source="$SRC/dist" ;;
            angular) source="$SRC/$OUT" ;;
            *) source="$SRC" ;;
          esac

          [ -d "$source" ] || {
            echo "Pasta para publicação não existe: $source" >&2
            exit 1
          }

          if [ "$TIPO" = react ] || [ "$TIPO" = angular ]; then
            [ -f "$source/index.html" ] || {
              echo "Build inválido: falta $source/index.html" >&2
              exit 1
            }
          fi

          workspace=$(realpath -e -- "$GITHUB_WORKSPACE")
          project=$(realpath -e -- "$SRC")
          published=$(realpath -e -- "$source")

          case "$project" in
            "$workspace"|"$workspace"/*) ;;
            *)
              echo "SRC fora do repositório: $SRC" >&2
              exit 1
              ;;
          esac

          case "$published" in
            "$project"/*) ;;
            "$project")
              if [ "$TIPO" = angular ]; then
                echo "OUT não pode ser o próprio SRC: $OUT" >&2
                exit 1
              fi
              ;;
            *)
              echo "Pasta para publicação fora de SRC: $source" >&2
              exit 1
              ;;
          esac

          [ ! -L "$DEPLOY_TARGET" ] || {
            echo "Destino simbólico proibido: $APP" >&2
            exit 1
          }

          mkdir -p -- "$DEPLOY_TARGET"

          # Arquivos excluídos não são publicados nem apagados no destino:
          # o .env e os dados existentes no servidor são preservados.
          rsync -a --delete \
            --exclude='.env*' \
            --exclude='.venv/' \
            --exclude='venv/' \
            --exclude='node_modules/' \
            --exclude='uploads/' \
            --exclude='storage/' \
            --exclude='private/' \
            --exclude='data/' \
            --exclude='.npmrc' \
            --exclude='.pypirc' \
            --exclude='.netrc' \
            --exclude='.git/' \
            --exclude='.github/' \
            "$published/" "$DEPLOY_TARGET/"

          echo "Aplicação publicada."

      - name: Preparar ambiente Python
        if: env.TIPO == 'python'
        run: |
          cd -- "$DEPLOY_TARGET"

          [ -x .venv/bin/python ] || python3 -m venv .venv

          .venv/bin/python -m pip install -r requirements.txt

      - name: Instalar dependências de produção
        if: env.TIPO == 'node'
        run: |
          cd -- "$DEPLOY_TARGET"

          npm ci --omit=dev --no-audit --no-fund

      - name: Gerar build e publicar Next.js
        if: env.TIPO == 'next'
        run: |
          build_root="$DEPLOY_BASE/.build"
          stage="$build_root/$APP"

          [ ! -L "$build_root" ] && [ ! -L "$stage" ] || {
            echo "Área de build simbólica proibida." >&2
            exit 1
          }

          [ ! -L "$DEPLOY_TARGET" ] || {
            echo "Destino simbólico proibido: $APP" >&2
            exit 1
          }

          umask 077
          mkdir -p -- "$stage"
          chmod 700 "$stage"

          rsync -a --no-perms --delete \
            --exclude='.env*' \
            --exclude='node_modules/' \
            --exclude='.next/' \
            --exclude='.npmrc' \
            --exclude='.pypirc' \
            --exclude='.netrc' \
            --exclude='.git/' \
            --exclude='.github/' \
            "$SRC/" "$stage/"

          find "$stage" -maxdepth 1 -name '.env*' -delete

          if [ -d "$DEPLOY_TARGET" ]; then
            rsync -a --no-perms \
              --include='/.env*' \
              --exclude='*' \
              "$DEPLOY_TARGET/" "$stage/"
          fi

          cd -- "$stage"

          npm install --no-audit --no-fund
          npm run build

          mkdir -p -- "$DEPLOY_TARGET"

          rsync -a --delete \
            --exclude='.env*' \
            --exclude='.venv/' \
            --exclude='venv/' \
            --exclude='uploads/' \
            --exclude='storage/' \
            --exclude='private/' \
            --exclude='data/' \
            --exclude='.npmrc' \
            --exclude='.pypirc' \
            --exclude='.netrc' \
            --exclude='.git/' \
            --exclude='.github/' \
            "$stage/" "$DEPLOY_TARGET/"

      - name: Reiniciar aplicação
        if: env.TIPO == 'python' || env.TIPO == 'node' || env.TIPO == 'next'
        run: |
          # Sem DEPLOY_USER, o PM2 é o do próprio usuário do runner.
          if [ -z "${DEPLOY_USER:-}" ] || [ "$DEPLOY_USER" = "$(id -un)" ]; then
            pm2_command=(pm2)
          else
            pm2_command=(sudo -n -H -u "$DEPLOY_USER" pm2)
          fi

          if ! processes=$("${pm2_command[@]}" jlist); then
            echo "Falha ao consultar os processos do PM2." >&2
            exit 1
          fi

          if ! status=$(printf '%s' "$processes" | python3 -c "$FIND_PROCESS"); then
            echo "Resposta inválida do PM2." >&2
            exit 1
          fi

          if [ "$status" = missing ]; then
            echo "Processo PM2 $APP ainda não configurado. Primeira publicação concluída."
            exit 0
          fi

          echo "Reiniciando o processo PM2 $APP..."
          "${pm2_command[@]}" restart "$APP"
          echo "Aplicação reiniciada."
        env:
          # Lê o JSON de "pm2 jlist" e diz se existe um processo chamado APP.
          FIND_PROCESS: >-
            import json, os, sys;
            processes = json.load(sys.stdin);
            isinstance(processes, list) or sys.exit("pm2 jlist não é uma lista");
            names = {p.get("name") for p in processes if isinstance(p, dict)};
            print("found" if os.environ["APP"] in names else "missing")
