from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
from tqdm.auto import tqdm
from config import api_keys_file

api_keys = [key for key in open(api_keys_file).read().split('\n') if key != '']
DEFAULT_API_KEY = api_keys[0]
DEFAULT_LLM = "meta-llama/Meta-Llama-3-70B-Instruct"


def get_llm_response(
        user_prompt: str, 
        system_prompt: str, 
        task_prompt=None, 
        messages=None,
        model_name=DEFAULT_LLM, 
        api_key=DEFAULT_API_KEY
    ):
    system_prompt += "\n" + task_prompt if task_prompt else system_prompt

    if messages is None:
        messages = []

    messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    client = openai.OpenAI(
            base_url = "https://api.endpoints.anyscale.com/v1",
            api_key=api_key
    )
    chat_completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0.7
    )

    response = chat_completion.choices[0].message.content  
    return response


def run_multithreaded_handler(obj_list, handler=get_llm_response, num_workers=10, ordered=False, *args, **kwargs):
    assert isinstance(obj_list, list) or isinstance(obj_list, dict), "obj_list must be a list or dict"
    responses = dict()
    progress_bar = tqdm(total=len(obj_list), desc="Processing", unit="task")
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        if isinstance(obj_list, list):
            future_to_obj = {executor.submit(handler, obj, *args, **kwargs): obj for obj in obj_list}
        else:
            future_to_obj = {executor.submit(handler, obj, *args, **kwargs): key for key, obj in obj_list.items()}
        
        for future in as_completed(future_to_obj):
            obj_key = future_to_obj[future]
            try:
                response = future.result()
                responses[obj_key] = response
            except Exception as exc:
                responses[obj_key] = "Not Available"
                print(f"Prompt generated an exception for obj {obj_key}: {exc}")
            finally:
                progress_bar.update(1)
    
    progress_bar.close()
    assert len(responses) == len(obj_list)
    
    return responses if ordered else list(responses.values())
