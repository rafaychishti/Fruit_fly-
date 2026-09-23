import pyarrow as pa
import pyarrow.compute as pc
import csv
import time

with open("circuit_root_ids.txt") as f:
    root_ids = set(int(line.strip()) for line in f if line.strip())
print(f"Loaded {len(root_ids)} candidate-circuit root IDs")

root_ids_array = pa.array(list(root_ids), type=pa.int64())

t0 = time.time()
mmap = pa.memory_map("proofread_connections_783.feather", "r")
reader = pa.ipc.open_file(mmap)
print(f"Total record batches: {reader.num_record_batches}")

matched_batches = []
total_rows = 0
for i in range(reader.num_record_batches):
    batch = reader.get_batch(i)
    total_rows += batch.num_rows
    pre_in = pc.is_in(batch.column("pre_pt_root_id"), value_set=root_ids_array)
    post_in = pc.is_in(batch.column("post_pt_root_id"), value_set=root_ids_array)
    mask = pc.or_(pre_in, post_in)
    if pc.any(mask).as_py():
        matched_batches.append(batch.filter(mask))
    if i % 50 == 0:
        print(f"  batch {i}/{reader.num_record_batches}, rows so far {total_rows}, matches so far {sum(b.num_rows for b in matched_batches)}, elapsed {time.time()-t0:.1f}s")

print(f"TOTAL rows scanned: {total_rows}")
if matched_batches:
    result_table = pa.Table.from_batches(matched_batches)
else:
    result_table = pa.table({name: pa.array([], type=field.type) for name, field in zip(reader.schema.names, reader.schema)})

print(f"Matched rows: {result_table.num_rows}")
print(f"Elapsed: {time.time()-t0:.1f}s")

out_path = "circuit_connectivity_filtered.csv"
df = result_table.to_pandas()
df.to_csv(out_path, index=False)
print(f"Wrote {out_path}, {len(df)} rows")

# quick summary
pre_is_dnp01 = df["pre_pt_root_id"].isin([720575940632499757, 720575940622838154])
post_is_dnp01 = df["post_pt_root_id"].isin([720575940632499757, 720575940622838154])
print(f"Rows with DNp01 as pre: {pre_is_dnp01.sum()}")
print(f"Rows with DNp01 as post: {post_is_dnp01.sum()}")
print(f"Rows with DNp01 as both pre and post (self-loop candidates): {(pre_is_dnp01 & post_is_dnp01).sum()}")
