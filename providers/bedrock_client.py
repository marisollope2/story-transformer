"""
AWS Bedrock Client Utility
Handles initialization and configuration of Bedrock clients
"""
import os
import boto3
from botocore.config import Config
from typing import Optional


def get_bedrock_client(region_name: Optional[str] = None, profile_name: Optional[str] = None):
    """
    Initialize and return a Bedrock runtime client.
    
    Args:
        region_name: AWS region (defaults to us-east-1 or from AWS config)
        profile_name: AWS profile name (optional)
    
    Returns:
        boto3 Bedrock runtime client
    """
    # Get region from environment or use default
    region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    # Configure retry strategy
    config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'adaptive'
        }
    )
    
    # Create session with optional profile
    if profile_name:
        session = boto3.Session(profile_name=profile_name)
        return session.client('bedrock-runtime', region_name=region, config=config)
    else:
        return boto3.client('bedrock-runtime', region_name=region, config=config)


def invoke_bedrock_model(
    client,
    model_id: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> str:
    """
    Invoke a Bedrock model with the given prompt.
    
    Args:
        client: Bedrock runtime client
        model_id: Model identifier (e.g., 'openai.gpt-oss-120b-1:0')
        prompt: User prompt
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 to 1.0)
        top_p: Top-p sampling parameter
    
    Returns:
        Generated text response
    """
    # Determine model provider based on model_id
    if model_id.startswith('openai.'):
        return _invoke_openai_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p)
    elif model_id.startswith('amazon.nova') or model_id.startswith('amazon.titan'):
        return _invoke_amazon_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p)
    elif model_id.startswith('meta.llama'):
        return _invoke_meta_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p)
    elif model_id.startswith('cohere.'):
        return _invoke_cohere_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p)
    elif model_id.startswith('mistral.'):
        return _invoke_mistral_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p)
    else:
        raise ValueError(f"Unsupported model: {model_id}")


def _invoke_openai_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p):
    """Invoke OpenAI models through Bedrock"""
    import json
    
    # Build messages array with system and user messages
    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # OpenAI models in Bedrock use a chat-like format.
    # Exclude chain-of-thought reasoning from the response (gpt-oss convention).
    body = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "reasoning": {"exclude": True}
    }
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Handle OpenAI response format
        if 'choices' in response_body and len(response_body['choices']) > 0:
            return response_body['choices'][0].get('message', {}).get('content', '')
        elif 'content' in response_body:
            return response_body['content']
        elif 'text' in response_body:
            return response_body['text']
        elif 'output' in response_body:
            # Some Bedrock OpenAI models may use different format
            if isinstance(response_body['output'], str):
                return response_body['output']
            elif isinstance(response_body['output'], dict):
                return response_body['output'].get('text', str(response_body['output']))
        else:
            return str(response_body)
            
    except Exception as e:
        raise Exception(f"Failed to invoke OpenAI model {model_id}: {str(e)}")


def _invoke_amazon_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p):
    """Invoke Amazon Nova/Titan models"""
    import json
    
    # Combine system prompt and user prompt
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    
    # Nova and Titan models use similar format but may have slight differences
    # Try the standard format first
    body = {
        "inputText": full_prompt,
        "textGenerationConfig": {
            "maxTokenCount": max_tokens,
            "temperature": temperature,
            "topP": top_p
        }
    }
    
    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Handle different response formats
        if 'results' in response_body and len(response_body['results']) > 0:
            return response_body['results'][0].get('outputText', '')
        elif 'outputText' in response_body:
            return response_body['outputText']
        elif 'completion' in response_body:
            return response_body['completion']
        else:
            # Try to extract text from any available field
            return str(response_body)
            
    except Exception as e:
        # If standard format fails, try alternative format for Nova models
        if model_id.startswith('amazon.nova'):
            # Alternative format for Nova models
            alternative_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": full_prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": top_p
                }
            }
            
            if system_prompt:
                alternative_body["system"] = [{"text": system_prompt}]
            
            try:
                response = client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(alternative_body),
                    contentType="application/json",
                    accept="application/json"
                )
                
                response_body = json.loads(response['body'].read())
                if 'output' in response_body and 'message' in response_body['output']:
                    content = response_body['output']['message'].get('content', [])
                    if isinstance(content, list) and len(content) > 0:
                        return content[0].get('text', '')
                
                return str(response_body)
            except:
                raise Exception(f"Failed to invoke model {model_id}: {str(e)}")
        else:
            raise Exception(f"Failed to invoke model {model_id}: {str(e)}")


def _invoke_meta_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p):
    """Invoke Meta Llama models"""
    import json
    
    # Build messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    body = {
        "prompt": f"<s>[INST] {system_prompt if system_prompt else ''}\n\n{prompt} [/INST]",
        "max_gen_len": max_tokens,
        "temperature": temperature,
        "top_p": top_p
    }
    
    # Alternative format for newer Llama models
    try:
        # Try the newer chat format first
        chat_body = {
            "messages": messages,
            "max_gen_len": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(chat_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        # Handle different response formats
        if 'generation' in response_body:
            return response_body['generation']
        elif 'content' in response_body and isinstance(response_body['content'], list):
            return response_body['content'][0].get('text', '')
        elif 'output' in response_body:
            return response_body['output']
        else:
            return str(response_body)
            
    except Exception as e:
        # Fallback to prompt format
        try:
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            if 'generation' in response_body:
                return response_body['generation']
            else:
                return str(response_body)
        except Exception as e2:
            raise Exception(f"Failed to invoke Meta model {model_id}: {str(e2)}")


def _invoke_cohere_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p):
    """Invoke Cohere models"""
    import json
    
    # Combine system prompt and user prompt
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"
    
    body = {
        "message": full_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "p": top_p,
        "stream": False
    }
    
    response = client.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )
    
    response_body = json.loads(response['body'].read())
    
    # Handle Cohere response format
    if 'generations' in response_body and len(response_body['generations']) > 0:
        return response_body['generations'][0].get('text', '')
    elif 'text' in response_body:
        return response_body['text']
    elif 'message' in response_body:
        return response_body['message'].get('text', '')
    else:
        return str(response_body)


def _invoke_mistral_model(client, model_id, prompt, system_prompt, max_tokens, temperature, top_p):
    """Invoke Mistral AI models"""
    import json
    
    # Build messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    body = {
        "prompt": f"<s>[INST] {system_prompt if system_prompt else ''}\n\n{prompt} [/INST]",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p
    }
    
    # Try chat format first (for newer Mistral models)
    try:
        chat_body = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(chat_body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'outputs' in response_body and len(response_body['outputs']) > 0:
            return response_body['outputs'][0].get('text', '')
        elif 'content' in response_body:
            return response_body['content']
        else:
            return str(response_body)
            
    except Exception as e:
        # Fallback to prompt format
        try:
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            if 'outputs' in response_body and len(response_body['outputs']) > 0:
                return response_body['outputs'][0].get('text', '')
            else:
                return str(response_body)
        except Exception as e2:
            raise Exception(f"Failed to invoke Mistral model {model_id}: {str(e2)}")

