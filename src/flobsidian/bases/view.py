from flobsidian.singleton import Singleton
from flobsidian.bases.filter import Filter
from flobsidian.bases.file_info import FileInfo
from flobsidian.messages import add_message
from flobsidian.utils import logger
import pandas as pd
from flobsidian.consts import MaxViewErrors


class View:

    def __init__(self, formulas, properties):
        self.type = ''
        self.name = ''
        self.filter: Filter = None
        self.order: list[str] = []
        self.sorts: list[tuple[str, str]] = []
        self.formulas: list = formulas
        self.properties: dict[str, dict] = properties

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
                prop_name = r.replace('.', '_')
                try:
                    prop = r.split('.')
                    if r in self.properties and 'displayName' in self.properties[
                            r]:
                        prop_name = self.properties[r]['displayName']

                    if prop[0] == 'formula':
                        value = self.formulas[prop[1]](f)
                    else:
                        value = f.get_prop(prop, render=True)
                except Exception as e:
                    if Singleton.config.vaults[
                            vault].base_config.error_on_field_parse:
                        raise ValueError(
                            f'could not infer value {r} from {f.path}: {e}')
                    else:
                        problems.append(
                            f'could not infer value {r} from {f.path}: {e}')
                        value = ''
                result[-1][prop_name] = value


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
        if len(df) > 0:
            columns_to_sort = []
            asc = []
            for s in self.sorts:
                s = s[0].replace('.', '_'), s[1]
                if s[0] not in df.columns or s[1] not in ['ASC', 'DESC']:
                    if Singleton.config.vaults[
                            vault].base_config.error_on_yaml_parse:
                        raise ValueError(f'Bad value for sorting: {s}')
                    else:
                        add_message(f'problems with sorting: {s}. Skipping', 1,
                                    vault)
                        continue
                columns_to_sort.append(s[0])
                asc.append(s[1] == 'ASC')
            if len(columns_to_sort) == 0:
                column = df.columns[0]
                columns_to_sort.append(column)
                asc.append(True)
                logger.warning('using defualt sorting')

        if len(columns_to_sort) > 0:
            df = df.sort_values(columns_to_sort, ascending=asc)
        else:
            add_message('The view is not sorted', 1, vault)
        return df.to_dict(orient="records")
