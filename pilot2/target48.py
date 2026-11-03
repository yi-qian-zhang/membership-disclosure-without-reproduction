"""Coordinate-correct hidden-48-nt evaluation of saved prefix predictions.

Historical DNABERT-2 predictions begin at the preceding BPE boundary. Keep
their generation protocol and saved strings; evaluate only the nominal target.
Missing generated letters are errors. This never restores withheld prefix letters.
"""
def target48(ex):
    n = ex.get('n_generated_nt')
    if n is None or int(n) == 48:
        return dict(ex)
    if int(n) < 48:
        raise ValueError('Saved comparison interval is shorter than the target')
    if 'pred_nt' not in ex or 'truth_nt' not in ex:
        raise ValueError('Cannot recrop without saved coordinate-aligned strings')
    d = int(n) - 48
    truth = ex['truth_nt'][d:d+48]
    pred = ex['pred_nt'][d:d+48]
    if len(truth) != 48:
        raise ValueError('Incomplete reference target')
    ham = sum(a != b for a,b in zip(pred,truth)) + 48-len(pred)
    out = dict(ex)
    out.update(exact=ham == 0, hamming_nt=ham, pred_nt=pred, truth_nt=truth,
               n_generated_nt=48, evaluation_endpoint='hidden48',
               boundary_cover_nt=int(n), boundary_cover_exact=ex['exact'],
               boundary_cover_hamming_nt=ex['hamming_nt'])
    return out
