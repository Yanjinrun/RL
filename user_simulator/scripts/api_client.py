"""
阿里百炼Qwen API客户端
"""
import json
import requests
from typing import Dict, Optional, List


class QwenAPIClient:
    """阿里百炼Qwen系列模型API客户端"""
    
    def __init__(self, api_key: str, base_url: str = None):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL，如果为None则使用默认值
        """
        self.api_key = api_key
        self.base_url = base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def call(self, 
             prompt: str, 
             model: str = "qwen-plus",
             temperature: float = 0.7,
             max_tokens: int = 2000,
             top_p: float = 0.8,
             **kwargs) -> str:
        """
        调用Qwen API生成文本
        
        Args:
            prompt: 输入提示词
            model: 模型名称，可选值: qwen-plus, qwen-max, qwen-turbo等
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            top_p: nucleus sampling参数
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                **kwargs
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 解析响应 - 兼容多种响应格式
            if "output" in result:
                output = result["output"]
                # 格式1: output.choices[0].message.content
                if "choices" in output and len(output["choices"]) > 0:
                    choice = output["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    elif "text" in choice:
                        return choice["text"]
                # 格式2: output.text
                elif "text" in output:
                    return output["text"]
                # 格式3: output.result
                elif "result" in output:
                    return output["result"]
            
            # 如果都没有，尝试直接获取text字段
            if "text" in result:
                return result["text"]
            
            # 如果还是找不到，抛出错误并显示完整响应
            raise ValueError(f"Unexpected API response format: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\nResponse: {json.dumps(error_detail, ensure_ascii=False, indent=2)}"
                except:
                    error_msg += f"\nResponse text: {e.response.text}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"Failed to parse API response: {str(e)}")
    
    def call_with_messages(self,
                           messages: List[Dict[str, str]],
                           model: str = "qwen-plus",
                           temperature: float = 0.7,
                           max_tokens: int = 2000,
                           top_p: float = 0.8,
                           **kwargs) -> str:
        """
        使用消息列表调用API（支持多轮对话）
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大生成token数
            top_p: nucleus sampling参数
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        payload = {
            "model": model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                **kwargs
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 解析响应 - 兼容多种响应格式
            if "output" in result:
                output = result["output"]
                # 格式1: output.choices[0].message.content
                if "choices" in output and len(output["choices"]) > 0:
                    choice = output["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    elif "text" in choice:
                        return choice["text"]
                # 格式2: output.text
                elif "text" in output:
                    return output["text"]
                # 格式3: output.result
                elif "result" in output:
                    return output["result"]
            
            # 如果都没有，尝试直接获取text字段
            if "text" in result:
                return result["text"]
            
            # 如果还是找不到，抛出错误并显示完整响应
            raise ValueError(f"Unexpected API response format: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\nResponse: {json.dumps(error_detail, ensure_ascii=False, indent=2)}"
                except:
                    error_msg += f"\nResponse text: {e.response.text}"
            raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"Failed to parse API response: {str(e)}")

