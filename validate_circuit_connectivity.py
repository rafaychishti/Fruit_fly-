import pandas as pd
import json

# -- load real neuron identity/side annotations --
neurons = pd.read_csv("circuit_candidate_neurons.tsv", sep="\t", dtype=str)
neurons["identified_type"] = neurons["cell_type"].where(neurons["cell_type"].str.len() > 0, neurons["hemibrain_type"])
neurons["root_id"] = neurons["root_id"].astype(str)

type_by_id = dict(zip(neurons["root_id"], neurons["identified_type"]))
side_by_id = dict(zip(neurons["root_id"], neurons["side"]))

lc4_ids = set(neurons.loc[neurons["identified_type"] == "LC4", "root_id"])
lplc2_ids = set(neurons.loc[neurons["identified_type"] == "LPLC2", "root_id"])
dnp01_ids = set(neurons.loc[neurons["identified_type"] == "DNp01", "root_id"])
all_316 = set(neurons["root_id"])

print("Identity counts from real annotation file:")
print(f"  LC4: {len(lc4_ids)}, LPLC2: {len(lplc2_ids)}, DNp01: {len(dnp01_ids)}, total: {len(all_316)}")
print(f"  DNp01 root IDs: {sorted(dnp01_ids)}")
print(f"  DNp01 sides: {[(rid, side_by_id[rid]) for rid in sorted(dnp01_ids)]}")
print()

# -- load filtered connectivity --
conn = pd.read_csv("circuit_connectivity_filtered.csv", dtype={"pre_pt_root_id": str, "post_pt_root_id": str})
print(f"Filtered connectivity rows: {len(conn)}")
print(f"Columns: {list(conn.columns)}")
print()

# -- item 2: direction verification --
# Cross-check: rows where pre in DNp01 and post in LC4/LPLC2 (reverse direction) --
# should be small/near-zero if pre->post really is upstream->downstream (feedforward: visual -> GF)
rev_gf_to_vis = conn[conn["pre_pt_root_id"].isin(dnp01_ids) & conn["post_pt_root_id"].isin(lc4_ids | lplc2_ids)]
fwd_vis_to_gf = conn[conn["pre_pt_root_id"].isin(lc4_ids | lplc2_ids) & conn["post_pt_root_id"].isin(dnp01_ids)]
print("DIRECTION CHECK (internal, data-derived, not assumed):")
print(f"  rows with pre in LC4/LPLC2, post in DNp01 (forward, visual->GF): {len(fwd_vis_to_gf)}, sum syn_count={fwd_vis_to_gf['syn_count'].sum()}")
print(f"  rows with pre in DNp01, post in LC4/LPLC2 (reverse, GF->visual): {len(rev_gf_to_vis)}, sum syn_count={rev_gf_to_vis['syn_count'].sum()}")
print()

# -- item 1 & 4: LC4->DNp01, LPLC2->DNp01 --
lc4_to_gf = conn[conn["pre_pt_root_id"].isin(lc4_ids) & conn["post_pt_root_id"].isin(dnp01_ids)]
lplc2_to_gf = conn[conn["pre_pt_root_id"].isin(lplc2_ids) & conn["post_pt_root_id"].isin(dnp01_ids)]

print("LC4 -> DNp01:")
print(f"  rows: {len(lc4_to_gf)}")
print(f"  total syn_count: {lc4_to_gf['syn_count'].sum()}")
print(f"  distinct presynaptic LC4 root IDs: {lc4_to_gf['pre_pt_root_id'].nunique()}")
print()
print("LPLC2 -> DNp01:")
print(f"  rows: {len(lplc2_to_gf)}")
print(f"  total syn_count: {lplc2_to_gf['syn_count'].sum()}")
print(f"  distinct presynaptic LPLC2 root IDs: {lplc2_to_gf['pre_pt_root_id'].nunique()}")
print()

# left/right breakdown (by presynaptic side, and by which DNp01 -- left/right -- is the target)
def side_breakdown(df, label):
    df = df.copy()
    df["pre_side"] = df["pre_pt_root_id"].map(side_by_id)
    df["post_side"] = df["post_pt_root_id"].map(side_by_id)
    print(f"{label} -- rows by (pre_side, post_side):")
    print(df.groupby(["pre_side", "post_side"]).agg(rows=("syn_count", "size"), total_syn=("syn_count", "sum")).to_string())
    print(f"{label} -- distinct presynaptic root IDs by pre_side:")
    print(df.groupby("pre_side")["pre_pt_root_id"].nunique().to_string())
    print()

side_breakdown(lc4_to_gf, "LC4->DNp01")
side_breakdown(lplc2_to_gf, "LPLC2->DNp01")

# -- item 3: reconcile 1577 --
all_incoming_to_dnp01 = conn[conn["post_pt_root_id"].isin(dnp01_ids)]
print(f"All rows with post in DNp01: {len(all_incoming_to_dnp01)}")
pre_in_lc4 = all_incoming_to_dnp01["pre_pt_root_id"].isin(lc4_ids)
pre_in_lplc2 = all_incoming_to_dnp01["pre_pt_root_id"].isin(lplc2_ids)
pre_other = ~(pre_in_lc4 | pre_in_lplc2)
print(f"  of which pre in LC4: {pre_in_lc4.sum()}")
print(f"  of which pre in LPLC2: {pre_in_lplc2.sum()}")
print(f"  of which pre is neither (other presynaptic neurons, outside our 316-id set or DNp01 itself): {pre_other.sum()}")
print(f"  check sum: {pre_in_lc4.sum()+pre_in_lplc2.sum()+pre_other.sum()} == {len(all_incoming_to_dnp01)}")
print()
# how many of the "other" are actually within our 316 set but not LC4/LPLC2/DNp01 (shouldn't be any, since our set IS lc4+lplc2+dnp01)
other_rows = all_incoming_to_dnp01[pre_other]
other_in_316 = other_rows["pre_pt_root_id"].isin(all_316)
print(f"  of 'other', how many pre IDs are still within our 316-set (sanity, should be 0 since 316=lc4+lplc2+dnp01): {other_in_316.sum()}")
print(f"  distinct 'other' presynaptic root IDs (true outside-circuit inputs to DNp01): {other_rows['pre_pt_root_id'].nunique()}")
print(f"  total syn_count from 'other' presynaptic neurons: {other_rows['syn_count'].sum()}")
print()

result = {
    "lc4_to_dnp01": {"rows": int(len(lc4_to_gf)), "total_syn_count": int(lc4_to_gf["syn_count"].sum()), "distinct_pre": int(lc4_to_gf["pre_pt_root_id"].nunique())},
    "lplc2_to_dnp01": {"rows": int(len(lplc2_to_gf)), "total_syn_count": int(lplc2_to_gf["syn_count"].sum()), "distinct_pre": int(lplc2_to_gf["pre_pt_root_id"].nunique())},
    "dnp01_incoming_total_rows": int(len(all_incoming_to_dnp01)),
    "dnp01_incoming_from_lc4_rows": int(pre_in_lc4.sum()),
    "dnp01_incoming_from_lplc2_rows": int(pre_in_lplc2.sum()),
    "dnp01_incoming_from_other_rows": int(pre_other.sum()),
    "dnp01_incoming_from_other_distinct_neurons": int(other_rows["pre_pt_root_id"].nunique()),
    "reverse_dnp01_to_visual_rows": int(len(rev_gf_to_vis)),
}
with open("validation_summary.json", "w") as f:
    json.dump(result, f, indent=2)
print("Wrote validation_summary.json")
print(json.dumps(result, indent=2))
