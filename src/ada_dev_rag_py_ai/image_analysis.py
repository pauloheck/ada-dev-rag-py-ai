import os
import logging
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch
from openai import OpenAI
import pytesseract
import base64

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Instanciar o cliente OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Carregar modelo e tokenizer para geração de legendas
model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

# Configurar o caminho do executável do Tesseract (ajuste conforme necessário)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Função para converter imagens para um formato suportado
def convert_image_format(image_file_path):
    try:
        with Image.open(image_file_path) as img:
            if img.format not in ['PNG', 'JPEG', 'JPG']:
                new_file_path = os.path.splitext(image_file_path)[0] + '.png'
                img.save(new_file_path, 'PNG')
                logging.info(f"Imagem convertida para {new_file_path}")
                return new_file_path
            return image_file_path
    except Exception as e:
        logging.error(f"Erro ao converter imagem: {e}")
        return None

# Função para gerar legenda da imagem
def generate_image_caption(image_file_path):
    try:
        image = Image.open(image_file_path)
        if image.mode != "RGB":
            image = image.convert(mode="RGB")
        pixel_values = feature_extractor(images=image, return_tensors="pt").pixel_values
        output_ids = model.generate(pixel_values, max_length=50, num_beams=4)
        caption = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        logging.info(f"Legenda gerada: {caption}")
        return caption
    except Exception as e:
        logging.error(f"Erro ao gerar legenda da imagem: {e}")
        return ""

# Função para processar a imagem usando OCR e gerar legenda
def process_image_with_model(image_file_path):
    try:
        # Extrair texto da imagem usando Tesseract OCR
        extracted_text = pytesseract.image_to_string(Image.open(image_file_path), lang='eng')
        logging.info(f"Texto extraído: {extracted_text}")
        
        # Gerar legenda da imagem usando modelo de image captioning
        caption = generate_image_caption(image_file_path)
        
        # Combinar os resultados
        combined_analysis = f"Texto extraído:\n{extracted_text}\n\nLegenda gerada:\n{caption}"
        return combined_analysis
    except Exception as e:
        logging.error(f"Erro ao processar a imagem: {e}")
        return ""

# Função para codificar a imagem em base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Função principal para analisar a imagem
def analyze_image(image_file_path, context=None):
    converted_path = convert_image_format(image_file_path)
    if not converted_path:
        return "Erro ao processar a imagem."

    # Obter análise da imagem
    image_analysis = process_image_with_model(converted_path)

    # Análise de contexto adicional usando OpenAI
    context_prompt = f"""
    Com base no texto extraído, forneça informações adicionais que possam enriquecer a compreensão do fluxo descrito. Considere aspectos técnicos, funcionais e contextuais relevantes.

    Texto extraído:
    {image_analysis}
    """

    try:
        # Chamada à API do OpenAI para buscar contexto adicional
        context_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em fornecer contexto adicional."},
                {"role": "user", "content": context_prompt}
            ],
            max_tokens=500,
            n=1,
            temperature=0.7,
        )
        additional_context = context_response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Erro ao buscar contexto adicional: {e}")
        additional_context = ""

    # Preparar o prompt para o GPT-4
    prompt = f"""
    Analise o diagrama fornecido e forneça uma descrição detalhada e formal do que está representado, incluindo:
    - O fluxo de informações ou operações mostrado, identificando claramente o início e o fim do fluxo.
    - Os participantes ou elementos visíveis (ex: pessoas, instituições, dispositivos) e suas funções.
    - A interação entre esses participantes ou elementos, destacando as conexões e transições entre eles.
    - Explique o processo ilustrado passo a passo de maneira detalhada, mencionando quaisquer setas ou linhas que indiquem direção ou sequência.
    - Forneça uma análise objetiva e confiável, evitando suposições e focando nos elementos visíveis e informações extraídas.
    Se necessário, mencione conexões técnicas ou funcionais.

    Informações da imagem:
    {image_analysis}
    """

    if context:
        prompt += f"\nContexto adicional: {context}"

    # Codificar a imagem
    image_base64 = encode_image_to_base64(converted_path)

    # Criar o conteúdo da mensagem com a imagem
    message_content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
    ]

    # Enviar a imagem e o texto para o OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em análise de imagens."},
                {"role": "user", "content": message_content}
            ],
            max_tokens=1500,
            n=1,
            temperature=0.7,
        )
        description = response.choices[0].message.content.strip()
        return description
    except Exception as e:
        logging.error(f"Erro ao chamar a API do OpenAI: {e}")
        return "Erro ao processar a imagem."

# Exemplo de uso
if __name__ == "__main__":
    image_path = "caminho/para/sua/imagem.png"  # Substitua pelo caminho da sua imagem
    resultado = analyze_image(image_path)
    print("Resultado da Análise:")
    print("="*50)
    print(resultado)
