import glob
from typing import List
import pathlib
import os

import pandas


def taxi_rides_paths() -> List[str]:
    dir = pathlib.Path(__file__).parent.resolve()
    pattern = os.path.join(dir, 'tmp/**/*.parquet')
    return glob.glob(pattern, recursive=True)


class PaTaxis:
    """
    """

    def __init__(self, backend=pandas) -> None:
        self.backend = backend
        paths = taxi_rides_paths()
        files = [self.backend.read_parquet(p) for p in paths]
        # Concatenate
        # https://pandas.pydata.org/docs/reference/api/pandas.concat.html?highlight=concat#pandas.concat
        self.df = self.backend.concat(files, ignore_index=True)
        self.cleanup()

    def cleanup(self):
        # Passenger count can't be zero or negative
        self.df['passenger_count'] = self.df['passenger_count'].mask(
            self.df['passenger_count'].lt(1), 1)

    def query1(self):
        selected_df = self.df[['vendor_id']]
        grouped_df = selected_df.groupby('vendor_id')
        final_df = grouped_df.size().reset_index()
        final_df.rename(
            columns={final_df.columns[-1]: 'counts'},
            inplace=True,
        )
        return final_df

    def query2(self):
        selected_df = self.df[['passenger_count', 'total_amount']]
        grouped_df = selected_df.groupby('passenger_count')
        final_df = grouped_df.mean().reset_index()
        return final_df

    def query3(self):
        selected_df = self.df[['passenger_count', 'pickup_at']]
        years = self.backend.to_datetime(
            self.df['pickup_at'],
            format='%Y-%m-%d %H:%M:%S',
        ).dt.year
        selected_df = self.backend.DataFrame({
            'passenger_count': selected_df['passenger_count'],
            'year': years,
        })
        grouped_df = selected_df.groupby(['passenger_count', 'year'])
        final_df = grouped_df.size().reset_index()
        final_df.rename(
            columns={final_df.columns[-1]: 'counts'},
            inplace=True,
        )
        return final_df

    def query4(self):
        selected_df = self.df[[
            'passenger_count',
            'pickup_at',
            'trip_distance',
        ]]
        distances = selected_df['trip_distance'].round().astype(int)
        years = self.backend.to_datetime(
            self.df['pickup_at'],
            format='%Y-%m-%d %H:%M:%S',
        ).dt.year
        selected_df = self.backend.DataFrame({
            'passenger_count': selected_df['passenger_count'],
            'year': years,
            'trip_distance': distances,
        })

        grouped_df = selected_df.groupby([
            'passenger_count',
            'year',
            'trip_distance',
        ])
        final_df = grouped_df.size().reset_index()
        final_df.rename(
            columns={final_df.columns[-1]: 'counts'},
            inplace=True,
        )
        final_df = final_df.sort_values(
            ['year', 'counts'],
            ascending=[True, False],
        )
        return final_df

    def log(self):
        print('Query 1:\n', self.query1())
        print('Query 2:\n', self.query2())
        print('Query 3:\n', self.query3())
        print('Query 4:\n', self.query4())


if __name__ == '__main__':
    PaTaxis().log()
