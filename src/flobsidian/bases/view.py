from flobsidian.singleton import Singleton
from flobsidian.bases.filter import Filter
from flobsidian.bases.file_info import FileInfo
from flobsidian.messages import add_message
from flobsidian.utils import logger
import pandas as pd
from flobsidian.consts import MaxViewErrors
from flobsidian.bases.cache import BaseCache
from flobsidian.consts import COVER_KEY
NAN_CONST = 0

def convert_field(x):
    if x is None:
        return float('nan')
    if not isinstance(x, (int, float, str, bool)):
        return str(x)
    else:
        return x


class View:

    def __init__(self, formulas, properties, base_path):
        self.type = ''
        self.name = ''
        self.filter: Filter = None
        self.order: list[str] = []
        self.sorts: list[tuple[str, str]] = []
        self.formulas: list = formulas
        self.properties: dict[str, dict] = properties
        self.base_path = base_path

    def gather_files(self, vault):
        files = [f for f in Singleton.indices[vault] if f.is_file()]
        files = [FileInfo(f, vault) for f in files]
        files = [f for f in files if self.filter.check(f)]
        return files

    def make_view(self, vault, force_refresh):
        if not force_refresh:
            cached, found_in_cache = BaseCache.get_from_cache(
                vault, self.base_path, self.name)
            if found_in_cache:
                return cached
        files = self.gather_files(vault)
        result = []
        problems = []
        order_list_plus_sort = set(self.order)
        is_numeric = {}
        for r in self.sorts:
            order_list_plus_sort.add(r[0])
        final_order = []
        if self.type == 'cards':
            order_list_plus_sort.add(COVER_KEY)
        for f in files:
            result.append({})
            for r in order_list_plus_sort:
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
                if r in self.order:
                    final_order.append(prop_name)
                value = convert_field(value)
                result[-1][prop_name] = value
                if prop_name not in is_numeric:
                    is_numeric[prop_name] = True

                if isinstance(value, str):
                    is_numeric[prop_name] = False

        if self.type == 'cards' and COVER_KEY not in final_order:
            final_order.append(COVER_KEY)

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
                for column in is_numeric:
                    if is_numeric[column]:
                        df[column] = pd.to_numeric(df[column], errors='coerce').fillna(NAN_CONST)
                    else:
                        df[column] = df[column].fillna('').astype(str)
                df = df.sort_values(
                    columns_to_sort,
                    ascending=asc)
            else:
                add_message('The view is not sorted', 1, vault)
        df = df[final_order]
        result = df.to_dict(orient="records")
        BaseCache.add_to_cache(vault, self.base_path, self.name, result)
        return result
