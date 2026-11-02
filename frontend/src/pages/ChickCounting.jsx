import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Camera, Upload, Target, Zap, Clock, History, Bird } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Button from "../components/Button";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { listBatches } from "../api/batches";
import { submitCountingSession, listCountingSessions } from "../api/monitoring";
import { extractErrorMessage, API_BASE_URL } from "../api/client";
import { formatDateTime } from "../lib/utils";

export default function ChickCounting() {
  const [batches, setBatches] = useState([]);
  const [batchesLoaded, setBatchesLoaded] = useState(false);
  const [batchId, setBatchId] = useState("");
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [naturalSize, setNaturalSize] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    listBatches().then((d) => {
      const list = d.results ?? d;
      setBatches(list);
      if (list.length) setBatchId(list[0].id);
      setBatchesLoaded(true);
    });
    listCountingSessions().then((d) => setHistory((d.results ?? d).slice(0, 6)));
  }, []);

  const onFileChange = (f) => {
    if (!f) return;
    setFile(f);
    setResult(null);
    setError("");
    setPreviewUrl(URL.createObjectURL(f));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !batchId) return;
    setLoading(true);
    setError("");
    try {
      const res = await submitCountingSession(batchId, file);
      setResult(res);
      listCountingSessions().then((d) => setHistory((d.results ?? d).slice(0, 6)));
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="UC-01 · AI Model"
        title="Chick Counting"
        description="Capture or upload a photo — we'll detect and count every chick automatically."
      />

      {batchesLoaded && batches.length === 0 ? (
        <Card>
          <EmptyState
            icon={Bird}
            title="Create a batch first"
            description="Chick counting needs a batch to attach results to. Add your first flock batch, then come back here."
            action={
              <Link
                to="/batches"
                className="text-sm font-semibold text-white bg-ink hover:bg-ink-dark px-4 py-2.5 rounded-xl transition-colors"
              >
                Go to Batches
              </Link>
            }
          />
        </Card>
      ) : (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block">
              <span className="block text-sm font-semibold text-ink-darker mb-1.5">Batch</span>
              <select
                value={batchId}
                onChange={(e) => setBatchId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-ink-light text-sm bg-white outline-none focus:border-ink/40"
              >
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>
                    Batch {b.batch_number}
                  </option>
                ))}
              </select>
            </label>

            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                onFileChange(e.dataTransfer.files?.[0]);
              }}
              className="relative border-2 border-dashed border-ink-light rounded-2xl overflow-hidden cursor-pointer hover:border-ink/30 transition-colors bg-ink-light/30 min-h-[16rem] flex items-center justify-center"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => onFileChange(e.target.files?.[0])}
              />
              {previewUrl ? (
                <div className="relative w-full">
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="w-full h-auto max-h-[26rem] object-contain"
                    onLoad={(e) =>
                      setNaturalSize({
                        w: e.target.naturalWidth,
                        h: e.target.naturalHeight,
                        renderW: e.target.width,
                        renderH: e.target.height,
                        offsetX: (e.target.parentElement.clientWidth - e.target.width) / 2,
                      })
                    }
                  />
                  {result?.boxes?.length > 0 && naturalSize && (
                    <div
                      className="absolute top-0 pointer-events-none"
                      style={{ left: naturalSize.offsetX, width: naturalSize.renderW, height: naturalSize.renderH }}
                    >
                      {/* Black box + white halo: yellow boxes were camouflaged
                          against the chicks themselves, which are yellow. The
                          halo keeps the box readable over dark litter too. */}
                      {result.boxes.map((box, i) => (
                        <div
                          key={i}
                          className="absolute border-2 border-ink-darker rounded-sm ring-1 ring-white/80"
                          style={{
                            left: `${(box.x / naturalSize.w) * 100}%`,
                            top: `${(box.y / naturalSize.h) * 100}%`,
                            width: `${(box.w / naturalSize.w) * 100}%`,
                            height: `${(box.h / naturalSize.h) * 100}%`,
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-10">
                  <span className="inline-flex h-12 w-12 rounded-full bg-white items-center justify-center mb-3">
                    <Upload size={20} className="text-ink" />
                  </span>
                  <p className="text-sm font-semibold text-ink-darker">
                    Click to upload, or drag a photo here
                  </p>
                  <p className="text-xs text-slate/50 mt-1">JPG or PNG</p>
                </div>
              )}
            </div>

            {error && <div className="text-sm text-rust bg-rust-light rounded-xl px-3.5 py-2.5">{error}</div>}

            <Button type="submit" disabled={!file || !batchId} loading={loading} className="w-full">
              <Camera size={16} />
              Run chick count
            </Button>
          </form>
        </Card>

        <div className="space-y-6">
          <Card>
            <h3 className="font-display text-base font-semibold text-ink-darker mb-4">Result</h3>
            {loading ? (
              <LoadingSpinner label="Analyzing image…" />
            ) : result ? (
              <div className="space-y-4">
                <div className="text-center py-2">
                  <div className="font-display text-5xl font-bold text-ink-darker">{result.count}</div>
                  <div className="text-sm text-slate/50 mt-1">chicks detected</div>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="bg-ink-light rounded-xl px-3 py-2.5 flex items-center gap-2">
                    <Target size={15} className="text-ink" />
                    <div>
                      <div className="text-xs text-slate/50">Confidence</div>
                      <div className="font-semibold text-ink-darker">
                        {(result.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  <div className="bg-ink-light rounded-xl px-3 py-2.5 flex items-center gap-2">
                    <Clock size={15} className="text-ink" />
                    <div>
                      <div className="text-xs text-slate/50">Processed in</div>
                      <div className="font-semibold text-ink-darker">{result.processing_time_ms}ms</div>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-slate/40 flex items-center gap-1.5">
                  <Zap size={12} /> {result.model_version}
                </p>
              </div>
            ) : (
              <EmptyState icon={Camera} title="No image yet" description="Upload a photo and run a count to see results here." />
            )}
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-3.5">
              <History size={15} className="text-slate/40" />
              <h3 className="font-display text-base font-semibold text-ink-darker">Recent sessions</h3>
            </div>
            {!history ? (
              <LoadingSpinner label="Loading…" />
            ) : history.length === 0 ? (
              <p className="text-sm text-slate/50">No counting sessions yet.</p>
            ) : (
              <ul className="space-y-3">
                {history.map((h) => (
                  <li key={h.id} className="flex items-center gap-3 text-sm">
                    <img
                      src={h.image?.startsWith("http") ? h.image : `${API_BASE_URL}${h.image}`}
                      alt=""
                      className="h-10 w-10 rounded-lg object-cover shrink-0 bg-ink-light"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold text-ink-darker">{h.count ?? "—"} chicks</div>
                      <div className="text-xs text-slate/45 truncate">{formatDateTime(h.created_at)}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
      )}
    </div>
  );
}
