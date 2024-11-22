import os

import pandas as pd
import psutil


def print_deep_mem_usage(df: pd.DataFrame, columns_info=True):
    """Prints `pd.DataFrame` deep memory usage in MB."""

    mem_usage = df.memory_usage(deep=True) / 1024 ** 2
    if columns_info:
        print('Memory usage in MB:')
        print(mem_usage.to_string(dtype=False))
    print(f'Total memory usage {mem_usage.sum():.1f} MB')


def get_process_memory_usage():
    """Returns a memory usage of the current process in bytes."""

    return psutil.Process(os.getpid()).memory_info().rss


def print_total_mem_usage(units='GB'):
    """Prints total memory usage."""

    mem_usage = get_process_memory_usage()  # in bytes

    if units == 'GB':
        mem_usage /= (1024 ** 3)
    else:
        units = 'MB'
        mem_usage /= (1024 ** 2)

    print(f'Process memory usage: {mem_usage:.2f} {units}')


def print_csr_mem_usage(csr_matrix):
    """Prints csr matrix memory usage in MB."""

    mem_usage_mb = (
        csr_matrix.data.nbytes
        + csr_matrix.indices.nbytes
        + csr_matrix.indptr.nbytes
    ) / (1024 ** 2)

    print(f'CSR mem usage: {mem_usage_mb:.2f} MB')
