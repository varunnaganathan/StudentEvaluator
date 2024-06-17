from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
from tqdm.auto import tqdm
from settings import api_keys_file
from prompting.templates import (
    STUDENT_QUALIFICATION_EVALUATION_SYSTEM_PROMPT
)

api_keys = [key for key in open(api_keys_file).read().split('\n') if key != '']
DEFAULT_API_KEY = api_keys[0]
DEFAULT_LLM = "meta-llama/Meta-Llama-3-70B-Instruct"


def get_llm_response(
        user_prompt, 
        task_prompt=None, 
        system_prompt=None, 
        model_name=DEFAULT_LLM, 
        api_key=DEFAULT_API_KEY
    ):
    sys_prompt = system_prompt if system_prompt else ""
    sys_prompt = sys_prompt + "\n" + task_prompt if task_prompt else sys_prompt

    sys_prompt = sys_prompt if sys_prompt else STUDENT_QUALIFICATION_EVALUATION_SYSTEM_PROMPT

    client = openai.OpenAI(
            base_url = "https://api.endpoints.anyscale.com/v1",
            api_key=api_key
    )
    chat_completion = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "system", "content": f"{system_prompt}"},
                {"role": "user", "content": user_prompt}],
        temperature=0.7
    )

    response = chat_completion.choices[0].message.content  
    return response


def get_llm_response_multithreaded(obj_list, handler, *args, num_workers=10):
    responses = list()
    progress_bar = tqdm(total=len(obj_list), desc="Processing", unit="task")
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_responses = [executor.submit(handler, obj, *args) for obj in obj_list]
    
        for future in as_completed(future_responses):
            try:
                response = future.result()
                responses.append(response)
            except Exception as exc:
                print(f"Prompt generated an exception: {exc}")
            finally:
                progress_bar.update(1)
    progress_bar.close()
    return responses