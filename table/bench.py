import os
from typing import List, Generator

import humanize
import numpy as np

from shared import Bench, run_persisted_benchmarks
from table.via_pandas import taxi_rides_paths

current_instance = None


def benchmarks_for_backend(class_: type, class_name: str, paths: List[str]) -> Generator[Bench, None, None]:

    def parse():
        global current_instance
        current_instance = class_(paths=paths)

    def q1():
        global current_instance
        if not isinstance(current_instance, class_):
            raise Exception('Uninitialized instance!')
        return current_instance.query1()

    def q2():
        global current_instance
        if not isinstance(current_instance, class_):
            raise Exception('Uninitialized instance!')
        return current_instance.query2()

    def q3():
        global current_instance
        if not isinstance(current_instance, class_):
            raise Exception('Uninitialized instance!')
        return current_instance.query3()

    def q4():
        global current_instance
        if not isinstance(current_instance, class_):
            raise Exception('Uninitialized instance!')
        return current_instance.query4()

    funcs = [parse, q1, q2, q3, q4]
    funcs_names = ['Parse', 'Query 1', 'Query 2', 'Query 3', 'Query 4']
    for func, func_name in zip(funcs, funcs_names):

        yield Bench(
            operation=func_name,
            backend=class_name,
            dataset=None,
            dataset_bytes=None,
            func=func,
        )

    global current_instance
    current_instance = None


def benchmarks_for_backends(backend_names: List[str],  paths: List[str]) -> Generator[Bench, None, None]:

    if 'Pandas' in backend_names:
        from table.via_pandas import ViaPandas
        yield from benchmarks_for_backend(ViaPandas, 'Pandas', paths)

    if 'Modin' in backend_names:
        from table.via_modin import ViaModin
        yield from benchmarks_for_backend(ViaModin, 'Modin', paths)

    if 'CuDF' in backend_names:
        from table.via_cudf import ViaCuDF
        yield from benchmarks_for_backend(ViaCuDF, 'CuDF', paths)

    if 'SQLite' in backend_names:
        from table.via_sqlite import ViaSQLite
        yield from benchmarks_for_backend(ViaSQLite, 'SQLite', paths)

    if 'Dask-CuDF' in backend_names:
        from table.via_dask_cudf import ViaDaskCuDF
        yield from benchmarks_for_backend(ViaDaskCuDF, 'Dask-CuDF', paths)

    if 'PySpark' in backend_names:
        from table.via_spark import ViaPySpark
        yield from benchmarks_for_backend(ViaPySpark, 'PySpark', paths)


def available_benchmarks(backend_names: List[str] = None) -> Generator[Bench, None, None]:

    # Validate passed argument
    if backend_names is None or len(backend_names) == 0:
        backend_names = [
            'Pandas',
            'Modin',
            'CuDF',
            'SQLite',
            # 'PySpark',
            # 'Dask-CuDF',
        ]
    if isinstance(backend_names, str):
        backend_names = backend_names.split(',')
    backend_names = [n.lower() for n in backend_names]

    # Prepare different dataset sizes
    all_paths = taxi_rides_paths()
    all_sizes = [os.path.getsize(p) for p in all_paths]
    total_size = sum(all_sizes)

    # Size categories are just different fractions of the entire dataset
    size_categories = [
        0.01,
        0.02,
        0.04,
        0.08,
        0.16,
        0.32,
        0.64,
        1.0,
    ]
    for size_category in size_categories:
        part_paths = []
        part_size = 0
        for p, s in zip(all_paths, all_sizes):
            part_paths.append(p)
            part_size += s
            if part_size / total_size >= size_category:
                break

        for s in benchmarks_for_backends(backend_names, part_paths):
            s.dataset_bytes = part_size
            s.dataset = humanize.naturalsize(part_size)
            yield s


if __name__ == '__main__':
    benches = list(available_benchmarks())
    backends = np.unique([x.backend for x in benches])
    datasets = np.unique([x.dataset for x in benches])

    print('Available backends: ', backends)
    print('Available datasets: ', datasets)
    run_persisted_benchmarks(benches, 10, 'table/report/results.json')
