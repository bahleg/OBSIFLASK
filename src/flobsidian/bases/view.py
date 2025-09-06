from flobsidian.singleton import Singleton
from flobsidian.bases.filter import Filter
from flobsidian.bases.file_info import FileInfo
from flobsidian.messages import add_message
from flobsidian.utils import logger
import pandas as pd
from flobsidian.consts import MaxViewErrors


class View:

    def __init__(self):
        self.type = ''
        self.name = ''
        self.filter: Filter = None
        self.order: list[str] = []

    def gather_files(self, vault):
        files = [f for f in Singleton.indices[vault] if f.is_file()]
        files = [FileInfo(f, vault) for f in files]
        files = [f for f in files if self.filter.check(f)]
        return files

    def make_view(self, vault):
        files = self.gather_files(vault)
        result = []
        problems = []
        for f in files:
            result.append({})
            for r in self.order:
                try:
                    value = f.get_prop(r.split('.'), render=True)
                except Exception as e:
                    if Singleton.config.vaults[
                            vault].base_config.error_on_field_parse:
                        raise ValueError(
                            f'could not find value {r} from {f.path}: {e}')
                    else:
                        problems.append(
                            f'could not find value {r} from {f.path}: {e}')
                        value = ''
                result[-1][r.replace('.', '_')] = value

        if problems:
            use_log = True
            if len(problems) > MaxViewErrors:
                for p in problems:
                    logger.warning(p)
                problems = problems[:MaxViewErrors] + [
                    '...', 'See  system logs'
                ]
                use_log = False

            add_message('problems during base rendering',
                        1,
                        vault,
                        '\n'.join(problems),
                        use_log=use_log)
        df = pd.DataFrame(result)
        return df.to_dict(orient="records")
