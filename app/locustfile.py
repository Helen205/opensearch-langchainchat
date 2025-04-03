from locust import HttpUser, task, between
import random
import time
from datetime import datetime
import gevent
from gevent import monkey
import pandas as pd
import os
from threading import Lock, Event
monkey.patch_all()

class ChatUser(HttpUser):
    wait_time = between(1, 2)
    test_results = []
    MAX_REQUESTS = 15
    _lock = Lock()
    test_running = True
    stop_event = Event()  
    
    def on_start(self):
        self.start_time = datetime.now()
        
    def save_results(self):
        try:
            if self.test_results:
                new_df = pd.DataFrame(self.test_results)
                
                columns = [
                    'load_balancer',
                    'ollama_num',
                    'context_length',
                    'response_time',
                    'model parameters',
                    'model',
                    'num_predict',
                    'users',
                    'model_size',
                    'RAM',
                    'GPU',
                    'question',
                    'response',
                    'error'
                ]
                
                new_df = new_df[columns]
                
                desktop = r"C:\Users\Helen\Desktop\python"
                filename = os.path.join(desktop, f"load_test_results.xlsx")
                
                try:
                    existing_df = pd.read_excel(filename, engine='openpyxl')
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                except FileNotFoundError:
                    combined_df = new_df
                
                combined_df.to_excel(filename, index=False, engine='openpyxl')
                
                print(f"Total requests processed: {self.environment.stats.total.num_requests}")
                print(f"Total rows in Excel: {len(combined_df)}")
                

                
        except Exception as e:
            print(f"Error saving results: {str(e)}")
    
    def should_stop_test(self):
        with self._lock:
            if self.environment.stats.total.num_requests >= self.MAX_REQUESTS:
                if not self.stop_event.is_set():  
                    self.test_running = False
                    print("\nReached maximum request limit. Stopping the test...")
                    self.save_results()
                    self.stop_event.set()
                    try:
                        self.environment.runner.quit()
                    except:
                        pass
                return True
            return False
    
    def on_stop(self):
        if not self.stop_event.is_set():
            self.test_running = False
            self.save_results()
            self.stop_event.set()
            try:
                self.environment.runner.quit()
            except:
                pass
    
    @task(1)
    def parallel_chat(self):
        if not self.test_running or self.should_stop_test():
            return
            
        questions = [
            "Flight search from Los Angeles to Paris with budget $520.0",
            "How much is a flight from London to Paris?",
            "Show my flight history",
            "I want to cancel my flight from Oslo to Miami",
            "Show flights from London to Paris",
            "Deactivate my ticket from London to Paris",
            "Change my ticket from London to Paris",
            "Give my ticket from İstanbul to Los Angeles to Helen",
            "buy a discounted ticket from Baku to Oslo",
            "buy a ticket from London to Paris with budget $520"
        ]
        
        threads = []
        for _ in range(2):
            if not self.test_running or self.should_stop_test():
                break
                
            question = random.choice(questions)
            thread = gevent.spawn(self.send_chat_request, question)
            threads.append(thread)
            time.sleep(0.5)
        
        for thread in threads:
            if self.test_running:
                thread.join()
    
    def send_chat_request(self, question):
        if not self.test_running or self.should_stop_test():
            return
            
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries and self.test_running:
            if self.should_stop_test():
                return
                
            try:
                chat_data = {
                    "user_query": question,
                    "username": "helenn",
                    "password": "1"
                }
                
                start_time = time.time()
                with self.client.post("/chat", json=chat_data, catch_response=True) as response:
                    end_time = time.time()
                    duration = (end_time - start_time) * 1000
                    
                    current_count = self.environment.stats.total.num_requests
                    print(f"\nRequest count: {current_count}/{self.MAX_REQUESTS}")
                    
                    result = pd.Series({
                        'load_balancer': 'ip-hash',
                        'ollama_num': 7,
                        'context_length': 2048,
                        'response_time': float(duration),
                        'model parameters': '494M',
                        'model': 'qwen:0.5b',
                        'num_predict': 1024,
                        'users': 20,
                        'model_size': '398MB',
                        'RAM': 'AMD Ryzen 7 8845HS',
                        'GPU': 'Radeon 780M Graphics(16 CPUs)',
                        'question': question,
                        'response': response.text if response.status_code == 200 else '',
                        'error': ''
                    })
                    
                    if response.status_code == 200:
                        if not self.test_running:
                            return
                        response.success()
                        self.test_results.append(result.to_dict())
                        print(f"Question: {question[:50]}...")
                        print(f"Response: {response.text}...")
                        print(f"Response Time: {duration:.2f}ms")
                        return
                    elif response.status_code == 429:
                        result['error'] = f"Rate limit error (429)"
                        wait_time = 2 ** retry_count
                        print(f"Rate limit hit, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        retry_count += 1
                    else:
                        result['error'] = f"HTTP Error {response.status_code}: {response.text}"
                        response.failure(f"Failed with status code: {response.status_code}")
                        self.test_results.append(result.to_dict())
                        print(f"Error Response Time: {duration:.2f}ms")
                        print(f"Error response: {response.text}")
                        retry_count += 1
                        
            except Exception as e:
                if not self.test_running:
                    return
                print(f"Exception occurred: {str(e)}")
                error_result = pd.Series({
                    'load_balancer': 'ip-hash',
                    'ollama_num': 7,
                    'context_length': 2048,
                    'response_time': float(duration),
                    'model parameters': '494M',
                    'model': 'qwen:0.5b',
                    'num_predict': 1024,
                    'users': 20,
                    'model_size': '398MB',
                    'RAM': 'AMD Ryzen 7 8845HS',
                    'GPU': 'Radeon 780M Graphics(16 CPUs)',
                    'question': question,
                    'response': '',
                    'error': str(e)
                })
                self.test_results.append(error_result.to_dict())
                retry_count += 1
                time.sleep(1)
        
        if retry_count >= max_retries:
            final_error = pd.Series({
                'load_balancer': 'ip-hash',
                'ollama_num': 7,
                'context_length': 2048,
                'response_time': float(duration),
                'model parameters': '494M',
                'model': 'qwen:0.5b',
                'num_predict': 1024,
                'users': 20,
                'model_size': '398MB',
                'RAM': 'AMD Ryzen 7 8845HS',
                'GPU': 'Radeon 780M Graphics(16 CPUs)',
                'question': question,
                'response': '',
                'error': f"Max retries reached after {max_retries} attempts"
            })
            self.test_results.append(final_error.to_dict())
            print(f"Max retries reached for question: {question[:50]}...")
