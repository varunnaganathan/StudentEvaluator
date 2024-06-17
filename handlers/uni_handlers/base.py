import importlib
from settings import uni_handlers
from handlers.base import UniversityDataHandler


uni_map = {
    'northumbria': "northumbria.NorthUmbriaWebDataHandler",
}

def get_uni_handler(uni_name) -> UniversityDataHandler:
    uni_name = uni_name.lower()
    uni_name = uni_name.replace(' ', '')
    if uni_name not in uni_map:
        raise ValueError(f'No handler for {uni_name}. Available handlers: {", ".join(uni_map.keys())}')
    
    pkg, cls = uni_map.get(uni_name).split('.')
    return getattr(importlib.import_module(f'{uni_handlers}.{pkg}'), cls)