

def find_sra_col(metadata, col=None, PREFIX='SRR'):
    def column_iter(md, col):
        column = md.get_column(col)
        if metadata.columns[col].type != "categorical":
            raise ValueError("`col` is not a categorical column.")
        yield column.drop_missing_values().to_series()

    def metadata_iter(md):
        md = md.filter_columns(column_type='categorical')
        for col in md.columns:
            yield from column_iter(md, col)

    if col is None:
        prelude = "No columns found with"
        series_iter = (s for s in metadata_iter(metadata))
    else:
        prelude = "Column %r does not have" % col
        series_iter = (s for s in column_iter(metadata, col))

    candidates = []
    leftover = []
    for series in series_iter:
        test = series.str.startswith(PREFIX)
        if not test.empty and test.all():
            candidates.append(series.name)
        elif test.any():
            leftover.append(series.name)

    if len(candidates) == 1:
        return candidates[0]

    elif not candidates:
        extra = ""
        if leftover:
            extra = (" These columns had some SRA-run styled accessions"
                     ", but contained unknown values as well: %r"
                     % (leftover,))
        raise ValueError(
            ("%s only SRA-run accessions (%s prefix)." % (prelude, PREFIX))
            + extra)
    else:
        raise ValueError("More than one column with SRA-run accessions"
                         " (%s prefix), use `col` to select one of them: %r"
                         % (PREFIX, candidates))




