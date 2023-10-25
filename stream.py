
class Stream:
	header = ""
	stream = ""
	def __init__(self,header:str='',stream:str=''):
		header = header.strip()
		stream = stream.strip()
	# TODO create proper title header
	def __setattr__(self, __name: str, __value: str) -> None:
		super().__setattr__(__name, __value.strip())
