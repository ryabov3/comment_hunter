import pandas as pd

class CommentSaver:
    def __init__(self, path=None):
        self.path: str = path
    
    def __call__(self, data, *args, **kwds):
        if self.path is None:
            df = pd.DataFrame(data)
            df = df.unstack().to_frame()
            df.columns = ['Comments']
            return df

        writer = pd.ExcelWriter(self.path)
        for street_name, comments in data.items():
            df = pd.DataFrame(data=comments, columns=['Comments'])
            df.to_excel(writer, index=False, sheet_name=street_name)
        writer.close()