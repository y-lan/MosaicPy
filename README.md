# MosaicPy

Modern Complement to Python's Standard Functions

MosaicPy is a compact yet meticulously designed library that enhances Python's standard functions. Initially created to streamline my own coding experience, this library aims to make life easier for Python developers by providing user-friendly utilities.

## Quick Start:
Install via pip:

```shell
pip install git+https://github.com/y-lan/mosaicpy.git
```

Example usage:
```python
import mosaicpy as mpy

# Process lists in parallel
mpy.pmap(list(range(100)), lambda x: x+1, show_progress=True)

# Call ChatGPT
mpy.OpenAIBot().chat('how to say {word} in chinese', word='hi')
```
