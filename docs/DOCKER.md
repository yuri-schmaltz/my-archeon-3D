# Guia de Uso do Docker - Archeon 3D

Este documento descreve como configurar e executar o **Archeon 3D** utilizando Docker e Docker Compose.

## Pré-requisitos

1. **Docker** instalado.
2. **NVIDIA Container Toolkit** instalado (necessário para suporte a GPU).
3. **Drivers NVIDIA** atualizados em sua máquina host.

## Instalação Facilitada (Recomendado)

Desenvolvemos um script automático que verifica seus drivers, configura o ambiente e fornece um menu interativo para gerenciar o Docker.

```bash
bash scripts/setup_docker.sh
```

Com este script, você pode construir a imagem, iniciar o Gradio ou a API, e ver logs sem precisar digitar comandos complexos do Docker.

## Configuração Manual

A forma mais simples de executar a aplicação é usando o Docker Compose.

### 1. Construir a Imagem e Iniciar os Serviços

Para iniciar a interface visual (**Gradio**) por padrão:

```bash
docker-compose up --build
```

### 2. Acessar a Aplicação

- **Interface Gradio**: [http://localhost:7860](http://localhost:7860)
- **Servidor de API**: [http://localhost:8000](http://localhost:8000)

## Executando como Servidor de API

Para rodar especificamente como um servidor de API, você pode sobrescrever o comando padrão no seu arquivo `docker-compose.yml` ou executando:

```bash
docker-compose run --rm -p 8081:8081 hunyuan3d python3 my_hunyuan_3d.py --api --host 0.0.0.0 --port 8081
```

## Configurações Principais (`docker-compose.yml`)

- **Volumes**:
  - `./gradio_cache`: Armazena modelos baixados e resultados temporários.
  - `./logs`: Armazena logs de execução.
- **Variáveis de Ambiente**:
  - `CUDA_VISIBLE_DEVICES`: Define qual GPU o contêiner deve usar (`0` por padrão).
  - `LOG_LEVEL`: Define o nível de detalhamento dos logs (`INFO`, `DEBUG`, etc.).

## Troubleshooting

### Problemas com a GPU
Se o contêiner não reconhecer a GPU, verifique se o comando abaixo funciona no seu terminal:
```bash
nvidia-smi
```
E se o suporte ao Docker está configurado:
```bash
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Espaço em Disco
As imagens Docker para modelos de IA podem ser grandes. Certifique-se de ter pelo menos 20GB de espaço livre para a imagem e os pesos dos modelos.
