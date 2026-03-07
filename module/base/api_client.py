"""
API 客户端模块
负责与 API 服务器进行所有HTTP交互
包括Bug日志上报、CL1数据提交和公告获取
支持主域名(nanoda.work)和备用域名(xf-sama.xyz)的自动故障转移
"""
import threading
from typing import Any, Dict, List, Tuple, Optional

import requests

from module.base.device_id import get_device_id
from module.logger import logger


class ApiClient:
    """统一的API客户端，支持双域名故障转移"""
    
    # 主域名和备用域名列表
    PRIMARY_DOMAIN = 'https://alas-apiv2.nanoda.work'
    FALLBACK_DOMAIN = 'https://alas-apiv2.xf-sama.xyz'
    
    # API端点路径
    BUG_LOG_PATH = '/api/post/bug'
    CL1_DATA_PATH = '/api/telemetry'
    ANNOUNCEMENT_PATH = '/api/get/announcement'
    STAMINA_REPORT_PATH = '/api/stamina/report'
    
    @classmethod
    def _get_endpoints(cls, path: str) -> List[str]:
        """
        获取指定路径的所有端点URL（主域名+备用域名）
        
        Args:
            path: API路径
            
        Returns:
            端点URL列表
        """
        return [
            f'{cls.PRIMARY_DOMAIN}{path}',
            f'{cls.FALLBACK_DOMAIN}{path}'
        ]
    
    @classmethod
    def _post_with_fallback(cls, path: str, json_data: Dict[str, Any], timeout: int = 5) -> Tuple[bool, int, str]:
        """
        使用故障转移机制发送POST请求
        
        Args:
            path: API路径
            json_data: 要发送的JSON数据
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, HTTP状态码, 响应文本)
        """
        return False, 0, last_error or 'Unknown error'
    
    @classmethod
    def _post_with_fallback(cls, path: str, json_data: Dict[str, Any], timeout: int = 5) -> Tuple[bool, int, str]:
        return cls._request_with_fallback('POST', path, json_data=json_data, timeout=timeout)
    
    @classmethod
    def _get_with_fallback(cls, path: str, params: Dict[str, Any] = None, timeout: int = 10) -> Tuple[bool, int, str]:
        """
        使用故障转移机制发送GET请求
        
        Args:
            path: API路径
            params: URL参数
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, HTTP状态码, 响应文本)
        """
        return cls._request_with_fallback('GET', path, params=params, timeout=timeout)

    @classmethod
    def _request_with_fallback(cls, method: str, path: str, params: Dict[str, Any] = None, 
                             json_data: Dict[str, Any] = None, timeout: int = 10,
                             success_codes: List[int] = None) -> Tuple[bool, int, str]:
        """
        通用请求方法，支持故障转移
        """
        if success_codes is None:
            success_codes = [200]
            
        endpoints = cls._get_endpoints(path)
        last_error = None
        
        for i, endpoint in enumerate(endpoints):
            try:
                domain_type = "主域名" if i == 0 else "备用域名"
                logger.debug(f'尝试使用{domain_type}: {endpoint}')
                
                if method == 'GET':
                    response = requests.get(
                        endpoint,
                        params=params,
                        timeout=timeout
                    )
                else:
                    response = requests.post(
                        endpoint,
                        json=json_data,
                        timeout=timeout,
                        headers={'Content-Type': 'application/json'}
                    )
                
                if response.status_code in success_codes:
                    if i > 0:
                        logger.info(f'✓ 使用{domain_type}请求成功')
                    return True, response.status_code, response.text
                else:
                    logger.warning(f'{domain_type}返回错误状态: {response.status_code}')
                    last_error = f'HTTP {response.status_code}'
                    
            except requests.exceptions.Timeout:
                logger.warning(f'{domain_type if i > 0 else "主域名"}请求超时')
                last_error = 'Timeout'
            except requests.exceptions.RequestException as e:
                logger.warning(f'{domain_type if i > 0 else "主域名"}请求失败: {e}')
                last_error = str(e)
            except Exception as e:
                logger.warning(f'{domain_type if i > 0 else "主域名"}发生异常: {e}')
                last_error = str(e)
        
        return False, 0, last_error or 'Unknown error'
    
    @staticmethod
    def _submit_bug_log(content: str, log_type: str):
        """
        内部方法：提交Bug日志
        
        Args:
            content: 日志内容
            log_type: 日志类型
        """
        try:
            device_id = get_device_id()
            data = {
                'device_id': device_id,
                'log_type': log_type,
                'log_content': content,
            }
            
            success, status_code, response_text = ApiClient._post_with_fallback(
                ApiClient.BUG_LOG_PATH,
                data,
                timeout=5
            )
            
            if success:
                logger.info(f'Bug log submitted: {content[:50]}...')
            else:
                logger.warning(f'Failed to submit bug log: {response_text}')
        except Exception as e:
            logger.warning(f'Failed to submit bug log: {e}')
    
    @classmethod
    def submit_bug_log(cls, content: str, log_type: str = 'warning', enabled: bool = True):
        """
        提交Bug日志（异步）
        
        Args:
            content: 日志内容
            log_type: 日志类型，默认为'warning'
            enabled: 是否启用上报，可传入 config.DropRecord_BugReport 配置值
        """
        if not enabled:
            return
        threading.Thread(
            target=cls._submit_bug_log,
            args=(content, log_type),
            daemon=True
        ).start()
    
    @staticmethod
    def _submit_cl1_data(data: Dict[str, Any], timeout: int):
        """
        内部方法：提交CL1数据
        
        Args:
            data: 数据字典
            timeout: 超时时间（秒）
        """
        try:
            # 如果没有任何战斗数据,不提交
            if data.get('battle_count', 0) == 0:
                logger.info('No CL1 battle data to submit')
                return
            
            logger.info(f'Submitting CL1 data for {data.get("month", "unknown")}...')
            logger.attr('battle_count', data.get('battle_count', 0))
            logger.attr('akashi_encounters', data.get('akashi_encounters', 0))
            logger.attr('akashi_probability', f"{data.get('akashi_probability', 0):.2%}")
            
            success, status_code, response_text = ApiClient._post_with_fallback(
                ApiClient.CL1_DATA_PATH,
                data,
                timeout=timeout
            )
            
            if success:
                logger.info('✓ CL1 data submitted successfully')
            else:
                logger.warning(f'✗ CL1 data submission failed: {response_text}')
        
        except Exception as e:
            logger.exception(f'Unexpected error during CL1 data submission: {e}')
    
    @classmethod
    def submit_cl1_data(cls, data: Dict[str, Any], timeout: int = 10):
        """
        提交CL1统计数据（异步）
        
        Args:
            data: 包含device_id和统计数据的字典
            timeout: 请求超时时间（秒），默认10秒
        """
        threading.Thread(
            target=cls._submit_cl1_data,
            args=(data, timeout),
            daemon=True
        ).start()
    
    @staticmethod
    def _report_stamina(stamina: float, timeout: int):
        """
        内部方法：上报体力到大盘
        
        Args:
            stamina: 当前体力值
            timeout: 超时时间（秒）
        """
        try:
            device_id = get_device_id()
            data = {
                'device_id': device_id,
                'stamina': int(stamina),
            }
            
            success, status_code, response_text = ApiClient._post_with_fallback(
                ApiClient.STAMINA_REPORT_PATH,
                data,
                timeout=timeout
            )
            
            if success:
                logger.info(f'CL1Data Updata Pass: {stamina}')
            else:
                logger.warning(f'CL1Data Updata Failed: {response_text}')
        
        except Exception as e:
            logger.exception(f'Unexpected error during stamina report: {e}')
    
    @classmethod
    def report_stamina(cls, stamina: float, timeout: int = 5):
        """
        上报当前体力到大盘（异步）
        
        Args:
            stamina: 当前体力值
            timeout: 请求超时时间（秒），默认5秒
        """
        threading.Thread(
            target=cls._report_stamina,
            args=(stamina, timeout),
            daemon=True
        ).start()
    
    @classmethod
    def get_announcement(cls, timeout: int = 1, current_id: int = None) -> Optional[Dict[str, Any]]:
        """
        获取公告信息（同步）
        
        Args:
            timeout: 请求超时时间（秒），默认10秒
            current_id: 当前公告ID，如果提供，用于增量检查
            
        Returns:
            公告数据字典，如果为None表示无更新或获取失败
        """
        import time
        try:
            # 添加时间戳参数以绕过缓存
            timestamp = int(time.time())
            params = {'t': timestamp}
            if current_id is not None:
                params['id'] = current_id            
            # 允许 200 (OK) 和 304 (Not Modified)
            success, status_code, response_text = cls._request_with_fallback(
                'GET',
                cls.ANNOUNCEMENT_PATH,
                params=params,
                timeout=timeout,
                success_codes=[200, 304]
            )            
            if success:
                # 304 或空内容表示无更新
                if status_code == 304 or not response_text.strip():
                    return None
                    
                import json
                try:
                    data = json.loads(response_text)
                    
                    # 如果返回空字典或无ID，也视为无更新
                    if not data or not data.get('announcementId'):
                        logger.info('公告数据为空或无ID')
                        return None
                        
                    # 只要有标题，且有内容 OR 链接，就是有效公告
                    if data.get('title') and (data.get('content') or data.get('url')):
                        return data
                    else:
                        return None
                except json.JSONDecodeError as e:
                    logger.warning(f'解析公告JSON失败: {e}, response={response_text[:100]}')
                    return None
            else:
                logger.warning(f'获取公告失败: {response_text}')
                return None
                
        except Exception as e:
            logger.warning(f'获取公告异常: {e}')
            return None

