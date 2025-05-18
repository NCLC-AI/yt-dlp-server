import os
import time
import uuid
import json
import threading
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TaskManager:
    """비동기 작업 관리자"""
    
    def __init__(self, download_dir):
        self.tasks = {}  # 작업 상태 저장
        self.download_dir = download_dir
        self.lock = threading.Lock()
        
        # 작업 상태 저장 디렉토리
        self.status_dir = os.path.join(download_dir, 'status')
        os.makedirs(self.status_dir, exist_ok=True)
        
        # 기존 작업 상태 복원
        self._restore_tasks()
        
    def _restore_tasks(self):
        """상태 파일에서 작업 상태 복원"""
        try:
            for filename in os.listdir(self.status_dir):
                if filename.endswith('.json'):
                    task_id = filename[:-5]  # .json 제거
                    file_path = os.path.join(self.status_dir, filename)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            task_data = json.load(f)
                            
                        # 파일이 존재하는지 확인
                        if task_data.get('status') == 'completed':
                            output_file = task_data.get('output_file')
                            if output_file and not os.path.exists(output_file):
                                task_data['status'] = 'failed'
                                task_data['error'] = 'Output file is missing'
                                
                        self.tasks[task_id] = task_data
                        logger.debug(f"Restored task {task_id}: {task_data['status']}")
                    except Exception as e:
                        logger.error(f"Failed to restore task {task_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to restore tasks: {str(e)}")
    
    def create_task(self, youtube_url: str, quality: str = '192') -> str:
        """새 작업 생성"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            'id': task_id,
            'youtube_url': youtube_url,
            'quality': quality,
            'status': 'pending',
            'created_at': time.time(),
            'updated_at': time.time(),
            'progress': 0,
            'output_file': None,
            'error': None,
            'title': None,
            'duration': None,
            'video_id': None
        }
        
        with self.lock:
            self.tasks[task_id] = task_data
            self._save_task_status(task_id)
        
        return task_id
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """작업 상태 조회"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            return task.copy()  # 복사본 반환
    
    def update_task(self, task_id: str, **updates) -> None:
        """작업 상태 업데이트"""
        with self.lock:
            if task_id not in self.tasks:
                return
            
            task = self.tasks[task_id]
            task.update(updates)
            task['updated_at'] = time.time()
            self._save_task_status(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        """작업 및 관련 파일 삭제"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            output_file = task.get('output_file')
            
            # 상태 파일 삭제
            status_file = os.path.join(self.status_dir, f"{task_id}.json")
            if os.path.exists(status_file):
                try:
                    os.remove(status_file)
                except Exception as e:
                    logger.error(f"Failed to delete status file for task {task_id}: {str(e)}")
            
            # 출력 파일 삭제 (있는 경우)
            if output_file and os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception as e:
                    logger.error(f"Failed to delete output file for task {task_id}: {str(e)}")
            
            # 연관된 정보 파일 삭제
            if output_file:
                video_id = os.path.splitext(os.path.basename(output_file))[0]
                info_file = os.path.join(self.download_dir, f"{video_id}.info.txt")
                if os.path.exists(info_file):
                    try:
                        os.remove(info_file)
                    except Exception as e:
                        logger.error(f"Failed to delete info file for task {task_id}: {str(e)}")
            
            # 작업 삭제
            del self.tasks[task_id]
            
            return True
    
    def _save_task_status(self, task_id: str) -> None:
        """작업 상태를 파일로 저장"""
        task = self.tasks.get(task_id)
        if not task:
            return
            
        status_file = os.path.join(self.status_dir, f"{task_id}.json")
        
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(task, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save task status for {task_id}: {str(e)}")
    
    def list_tasks(self) -> list:
        """모든 작업 목록 반환"""
        with self.lock:
            return [task.copy() for task in self.tasks.values()]