

class NameGenerator:
    __slots__ = ("last_name", )

    def __init__(self):
        self.last_name = 'a'*6  # последнее сгенерированное имя

    def generated(self, name: str) -> bool:
        for i in name:
            if ord('a') > ord(i) or ord(i) > ord('z'):
                return False

        if len(name) < 6:
            return False
        elif len(name) < len(self.last_name):
            return True
        elif len(name) > len(self.last_name):
            return False

        # длинна как у последнего сгенерированного элемента
        for a, b in zip(name, self.last_name):
            if ord(a) > ord(b):
                return False

        return True

    def __next__(self) -> str:
        for i in range(len(self.last_name)):
            if self.last_name[i] != 'z':
                self.last_name = self.last_name[:i] + chr(ord(self.last_name[i]) + 1) + self.last_name[i + 1:]
                break
        else:
            self.last_name = 'a' * (len(self.last_name) + 1)

        return self.last_name
