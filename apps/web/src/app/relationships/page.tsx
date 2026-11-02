"use client";

import { getApiBaseUrl } from "@/lib/api";
import React, { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import type { Core, NodeSingular, EdgeSingular, EventObject, ElementDefinition, StylesheetStyle, LayoutOptions } from "cytoscape";
import { AppHeader } from "@/components/navigation/AppHeader";

interface GraphNodeData {
  id: string;
  label: string;
  name?: string;
  node_type: string;
  category?: string;
  status?: string;
  amount?: number;
  cadence?: string;
}

interface RawNodePayload {
  data: GraphNodeData;
}

interface RawEdgePayload {
  data: {
    id: string;
    source: string;
    target: string;
    relationship_type: string;
    label?: string;
  };
}

interface GraphHealth {
  status: string;
  enabled: boolean;
  connected: boolean;
  uri?: string;
  database?: string;
  node_count?: number;
  edge_count?: number;
  message?: string;
}

interface GraphSummary {
  total_nodes: number;
  total_relationships: number;
  counts_by_label?: Record<string, number>;
  counts_by_relationship?: Record<string, number>;
  last_sync_timestamp?: string | null;
}

const PALETTE = {
  navyDark: "#011633",
  navyCard: "#031B38",
  navyBorder: "#164B68",
  navyHighlight: "#082746",
  amber: "#FFA52B",
  amberBorder: "#F08A00",
  teal: "#00B8C7",
  tealBorder: "#00E0E0",
  cyan: "#00E0E0",
  rose: "#F43F5E",
  pearl: "#F4F7FB",
  slate: "#A9BBCD",
};

export default function RelationshipExplorerPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const [health, setHealth] = useState<GraphHealth | null>(null);
  const [summary, setSummary] = useState<GraphSummary | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeLayout, setActiveLayout] = useState<string>("cose");

  const apiBase = getApiBaseUrl();

  // Initialize Cytoscape and render elements
  const renderCytoscape = useCallback(
    async (nodes: RawNodePayload[], edges: RawEdgePayload[]) => {
      if (!containerRef.current || typeof window === "undefined") return;

      const cytoscapeLib = (await import("cytoscape")).default;

      if (cyRef.current) {
        cyRef.current.destroy();
      }

      const elements: ElementDefinition[] = [
        ...nodes.map((n) => ({
          group: "nodes" as const,
          data: n.data,
        })),
        ...edges.map((e) => ({
          group: "edges" as const,
          data: e.data,
        })),
      ];

      const cy = cytoscapeLib({
        container: containerRef.current,
        elements,
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              color: PALETTE.pearl,
              "font-size": "11px",
              "font-weight": "bold",
              "text-valign": "center",
              "text-halign": "center",
              "text-wrap": "wrap",
              "text-max-width": "90px",
              width: 44,
              height: 44,
              "border-width": 2,
              "border-color": PALETTE.navyBorder,
              "background-color": PALETTE.navyHighlight,
            },
          },
          {
            selector: "node[node_type = 'User']",
            style: {
              "background-color": PALETTE.pearl,
              color: PALETTE.navyDark,
              "border-color": PALETTE.teal,
              "border-width": 3,
              shape: "round-rectangle",
              width: 60,
              height: 38,
            },
          },
          {
            selector: "node[node_type = 'Merchant']",
            style: {
              "background-color": PALETTE.amber,
              color: PALETTE.navyDark,
              "border-color": PALETTE.amberBorder,
              "border-width": 3,
              shape: "round-rectangle",
              width: 56,
              height: 48,
            },
          },
          {
            selector: "node[node_type = 'Commitment']",
            style: {
              "background-color": PALETTE.teal,
              color: PALETTE.navyDark,
              "border-color": PALETTE.tealBorder,
              "border-width": 3,
              shape: "ellipse",
              width: 52,
              height: 52,
            },
          },
          {
            selector: "node[node_type = 'Transaction']",
            style: {
              "background-color": PALETTE.navyHighlight,
              color: PALETTE.cyan,
              "border-color": PALETTE.cyan,
              "border-width": 2,
              shape: "ellipse",
              width: 36,
              height: 36,
              "font-size": "9px",
            },
          },
          {
            selector: "node[node_type = 'CommitmentInsight']",
            style: {
              "background-color": PALETTE.rose,
              color: "#FFFFFF",
              "border-color": "#FDA4AF",
              "border-width": 2,
              shape: "diamond",
              width: 42,
              height: 42,
            },
          },
          {
            selector: "node[node_type = 'DescriptorAlias']",
            style: {
              "background-color": PALETTE.navyBorder,
              color: PALETTE.slate,
              "border-color": PALETTE.navyHighlight,
              shape: "round-tag",
              width: 38,
              height: 32,
              "font-size": "9px",
            },
          },
          {
            selector: "edge",
            style: {
              width: 2,
              "line-color": PALETTE.navyBorder,
              "target-arrow-color": PALETTE.teal,
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              "arrow-scale": 0.8,
              label: "data(label)",
              "font-size": "8px",
              color: PALETTE.slate,
              "text-rotation": "autorotate",
              "text-margin-y": -6,
            },
          },
          {
            selector: "node:selected",
            style: {
              "border-color": "#FFFFFF",
              "border-width": 4,
            },
          },
        ] as unknown as StylesheetStyle[],
        layout: {
          name: activeLayout,
          padding: 40,
        } as LayoutOptions,
      });

      cy.on("tap", "node", (evt: EventObject) => {
        const node = evt.target as NodeSingular;
        setSelectedNode(node.data() as GraphNodeData);
      });

      cy.on("tap", (evt: EventObject) => {
        if (evt.target === cy) {
          setSelectedNode(null);
        }
      });

      cyRef.current = cy;
    },
    [activeLayout]
  );

  // Initial load
  useEffect(() => {
    let active = true;

    async function fetchData() {
      try {
        const [hRes, sRes, eRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/graph/health`),
          fetch(`${apiBase}/api/v1/graph/summary`),
          fetch(`${apiBase}/api/v1/graph/explorer`),
        ]);

        if (!active) return;

        if (hRes.ok) {
          const hData: GraphHealth = await hRes.json();
          setHealth(hData);
        }
        if (sRes.ok) {
          const sData: GraphSummary = await sRes.json();
          setSummary(sData);
        }
        if (eRes.ok) {
          const elements = await eRes.json();
          if (active) {
            await renderCytoscape(elements.nodes || [], elements.edges || []);
          }
        }
      } catch (err) {
        console.error("Failed to fetch graph data:", err);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      active = false;
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [apiBase, renderCytoscape]);

  // Node filtering
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    cy.batch(() => {
      if (filterType === "ALL") {
        cy.nodes().style("display", "element");
        cy.edges().style("display", "element");
      } else {
        cy.nodes().forEach((n: NodeSingular) => {
          if (n.data("node_type") === filterType || n.data("node_type") === "User") {
            n.style("display", "element");
          } else {
            n.style("display", "none");
          }
        });
        cy.edges().forEach((e: EdgeSingular) => {
          if (e.source().visible() && e.target().visible()) {
            e.style("display", "element");
          } else {
            e.style("display", "none");
          }
        });
      }
    });
  }, [filterType]);

  // Search highlighting
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cyRef.current || !searchQuery.trim()) return;

    const cy = cyRef.current;
    const q = searchQuery.toLowerCase();
    const matched = cy.nodes().filter((n: NodeSingular) => {
      const label = (n.data("label") || "").toLowerCase();
      const name = (n.data("name") || "").toLowerCase();
      return label.includes(q) || name.includes(q);
    });

    if (matched.length > 0) {
      cy.elements().unselect();
      matched.select();
      cy.animate({
        center: { eles: matched },
        zoom: 1.4,
        duration: 400,
      });
      setSelectedNode(matched.first().data() as GraphNodeData);
    }
  };

  // Sync handler
  const handleSync = async () => {
    try {
      setSyncing(true);
      setSyncMsg(null);
      const res = await fetch(`${apiBase}/api/v1/graph/sync`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setSyncMsg(
          `Sync successful: ${data.nodes_synced} nodes, ${data.relationships_synced} relationships updated (${data.execution_time_ms}ms)`
        );
        // Refresh summary and elements
        const [sRes, eRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/graph/summary`),
          fetch(`${apiBase}/api/v1/graph/explorer`),
        ]);
        if (sRes.ok) setSummary(await sRes.json());
        if (eRes.ok) {
          const elements = await eRes.json();
          await renderCytoscape(elements.nodes || [], elements.edges || []);
        }
      } else {
        setSyncMsg(`Sync error: ${data.detail || "Unknown error"}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Sync request failed";
      setSyncMsg(`Sync failed: ${message}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 30);
  const handleReset = () => {
    if (!cyRef.current) return;
    const layout = cyRef.current.layout({ name: activeLayout } as LayoutOptions);
    layout.run();
  };

  return (
    <div className="min-h-screen bg-[#011633] text-white flex flex-col">
      <AppHeader />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Top Header Card */}
        <div className="bg-[#031B38] border border-[#164B68] rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-2xl">🕸️</span>
              <h1 className="text-2xl font-bold tracking-tight text-white">Relationship Intelligence</h1>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${
                  health?.connected
                    ? "bg-emerald-950 text-emerald-400 border-emerald-600/50"
                    : "bg-[#082746] text-[#FFA52B] border-[#F08A00]/40"
                }`}
              >
                {health?.connected ? "Neo4j Active" : "Relational Projection Mode"}
              </span>
            </div>
            <p className="text-xs text-[#A9BBCD] mt-1">
              Multi-hop topological projection of recurring commitments, merchant descriptors, transactions, and anomaly evidence.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleSync}
              disabled={syncing}
              className="px-4 py-2 bg-gradient-to-r from-[#FFA52B] to-[#F08A00] text-[#011633] hover:brightness-110 font-bold rounded-lg text-xs transition-all shadow flex items-center gap-2 disabled:opacity-50"
            >
              {syncing ? (
                <>
                  <span className="inline-block animate-spin">⟳</span> Synchronizing...
                </>
              ) : (
                <>
                  <span>🔄</span> Sync Graph Projection
                </>
              )}
            </button>
          </div>
        </div>

        {/* Sync message feedback */}
        {syncMsg && (
          <div className="p-3 bg-[#082746] border border-[#164B68] rounded-xl text-xs text-[#00E0E0] flex items-center justify-between">
            <span>{syncMsg}</span>
            <button onClick={() => setSyncMsg(null)} className="text-[#A9BBCD] hover:text-white">✕</button>
          </div>
        )}

        {/* Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-[#031B38] border border-[#164B68] p-4 rounded-xl">
            <div className="text-[11px] uppercase tracking-wider text-[#A9BBCD]">Graph Nodes</div>
            <div className="text-2xl font-black text-[#00E0E0] mt-1">{summary?.total_nodes ?? 0}</div>
            <div className="text-[10px] text-[#A9BBCD] mt-0.5">Entities represented</div>
          </div>
          <div className="bg-[#031B38] border border-[#164B68] p-4 rounded-xl">
            <div className="text-[11px] uppercase tracking-wider text-[#A9BBCD]">Relationships</div>
            <div className="text-2xl font-black text-[#FFA52B] mt-1">{summary?.total_relationships ?? 0}</div>
            <div className="text-[10px] text-[#A9BBCD] mt-0.5">Multi-hop links</div>
          </div>
          <div className="bg-[#031B38] border border-[#164B68] p-4 rounded-xl">
            <div className="text-[11px] uppercase tracking-wider text-[#A9BBCD]">Merchants</div>
            <div className="text-2xl font-black text-white mt-1">{summary?.counts_by_label?.Merchant ?? 22}</div>
            <div className="text-[10px] text-[#A9BBCD] mt-0.5">Canonical entities</div>
          </div>
          <div className="bg-[#031B38] border border-[#164B68] p-4 rounded-xl">
            <div className="text-[11px] uppercase tracking-wider text-[#A9BBCD]">Commitments</div>
            <div className="text-2xl font-black text-[#00B8C7] mt-1">{summary?.counts_by_label?.Commitment ?? 12}</div>
            <div className="text-[10px] text-[#A9BBCD] mt-0.5">Recurring pipelines</div>
          </div>
        </div>

        {/* Interactive Explorer Container */}
        <div className="bg-[#031B38] border border-[#164B68] rounded-2xl overflow-hidden shadow-2xl flex flex-col">
          {/* Controls Bar */}
          <div className="p-4 border-b border-[#164B68] bg-[#021429] flex flex-wrap items-center justify-between gap-3 text-xs">
            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[#A9BBCD] font-medium mr-1">Filter:</span>
              {[
                { label: "All Nodes", type: "ALL" },
                { label: "Merchants", type: "Merchant" },
                { label: "Commitments", type: "Commitment" },
                { label: "Transactions", type: "Transaction" },
                { label: "Insights", type: "CommitmentInsight" },
              ].map((pill) => (
                <button
                  key={pill.type}
                  onClick={() => setFilterType(pill.type)}
                  className={`px-2.5 py-1 rounded-md transition-all font-medium ${
                    filterType === pill.type
                      ? "bg-[#082746] text-[#FFA52B] border border-[#F08A00]/50"
                      : "text-[#A9BBCD] hover:bg-[#082746]/40 hover:text-white border border-transparent"
                  }`}
                >
                  {pill.label}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <form onSubmit={handleSearch} className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Search node..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-[#082746] border border-[#164B68] rounded-lg px-3 py-1 text-xs text-white placeholder-[#A9BBCD] focus:outline-none focus:border-[#00B8C7]"
              />
              <button
                type="submit"
                className="px-3 py-1 bg-[#164B68] hover:bg-[#0B3152] text-white rounded-lg transition-colors font-medium"
              >
                Find
              </button>
            </form>

            {/* Layout selector & Zoom Controls */}
            <div className="flex items-center gap-2">
              <select
                value={activeLayout}
                onChange={(e) => setActiveLayout(e.target.value)}
                className="bg-[#082746] border border-[#164B68] rounded-lg px-2 py-1 text-xs text-white focus:outline-none"
              >
                <option value="cose">Force Directed</option>
                <option value="concentric">Concentric</option>
                <option value="circle">Circular</option>
              </select>

              <div className="flex items-center border border-[#164B68] rounded-lg overflow-hidden bg-[#082746]">
                <button
                  onClick={handleZoomIn}
                  className="px-2.5 py-1 hover:bg-[#164B68] text-white font-bold border-r border-[#164B68]"
                  title="Zoom In"
                >
                  +
                </button>
                <button
                  onClick={handleZoomOut}
                  className="px-2.5 py-1 hover:bg-[#164B68] text-white font-bold border-r border-[#164B68]"
                  title="Zoom Out"
                >
                  −
                </button>
                <button
                  onClick={handleFit}
                  className="px-2.5 py-1 hover:bg-[#164B68] text-xs text-[#A9BBCD] hover:text-white border-r border-[#164B68]"
                  title="Fit to Canvas"
                >
                  Fit
                </button>
                <button
                  onClick={handleReset}
                  className="px-2.5 py-1 hover:bg-[#164B68] text-xs text-[#A9BBCD] hover:text-white"
                  title="Reset Layout"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          {/* Graph Viewport + Side Inspector */}
          <div className="relative w-full h-[640px] bg-[#021024]">
            {loading && (
              <div className="absolute inset-0 z-20 bg-[#011633]/80 flex flex-col items-center justify-center gap-3">
                <span className="text-3xl animate-spin">⟳</span>
                <span className="text-sm font-semibold text-[#00E0E0]">Loading Relationship Topology...</span>
              </div>
            )}

            {/* Cytoscape Canvas */}
            <div ref={containerRef} className="w-full h-full" />

            {/* Node Inspector Drawer */}
            {selectedNode && (
              <div className="absolute top-4 right-4 z-10 w-80 bg-[#031B38]/95 border border-[#164B68] rounded-xl p-4 shadow-2xl backdrop-blur-md">
                <div className="flex items-center justify-between pb-3 border-b border-[#164B68]">
                  <span className="text-xs uppercase font-bold tracking-wider text-[#00E0E0]">
                    {selectedNode.node_type} Inspector
                  </span>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="text-[#A9BBCD] hover:text-white text-xs px-1"
                  >
                    ✕
                  </button>
                </div>

                <div className="mt-3 space-y-2.5 text-xs">
                  <div>
                    <div className="text-[10px] uppercase text-[#A9BBCD]">Label / Entity</div>
                    <div className="text-sm font-bold text-white mt-0.5">{selectedNode.label || selectedNode.name}</div>
                  </div>

                  {selectedNode.amount !== undefined && (
                    <div>
                      <div className="text-[10px] uppercase text-[#A9BBCD]">Value</div>
                      <div className="text-base font-black text-[#FFA52B] mt-0.5">
                        ₹{selectedNode.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  )}

                  {selectedNode.cadence && (
                    <div>
                      <div className="text-[10px] uppercase text-[#A9BBCD]">Cadence</div>
                      <div className="text-xs font-semibold text-[#00E0E0] capitalize">{selectedNode.cadence}</div>
                    </div>
                  )}

                  {selectedNode.category && (
                    <div>
                      <div className="text-[10px] uppercase text-[#A9BBCD]">Category</div>
                      <div className="text-xs text-white">{selectedNode.category}</div>
                    </div>
                  )}

                  {selectedNode.status && (
                    <div>
                      <div className="text-[10px] uppercase text-[#A9BBCD]">Status / Severity</div>
                      <span className="inline-block mt-0.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-[#082746] text-[#FFA52B] border border-[#F08A00]/40 capitalize">
                        {selectedNode.status}
                      </span>
                    </div>
                  )}

                  <div className="pt-2 border-t border-[#164B68] text-[10px] text-[#A9BBCD]">
                    <span>Node ID: </span>
                    <span className="font-mono text-white select-all">{selectedNode.id}</span>
                  </div>

                  {/* Deep Navigation Links */}
                  {selectedNode.node_type === "Commitment" && (
                    <Link
                      href={`/commitments/${selectedNode.id}`}
                      className="block text-center mt-3 py-1.5 bg-[#00B8C7] hover:bg-[#00E0E0] text-[#011633] font-bold rounded-lg text-xs transition-colors"
                    >
                      View Commitment Details →
                    </Link>
                  )}

                  {selectedNode.node_type === "Merchant" && (
                    <Link
                      href={`/merchants/${selectedNode.id}`}
                      className="block text-center mt-3 py-1.5 bg-[#FFA52B] hover:bg-[#F08A00] text-[#011633] font-bold rounded-lg text-xs transition-colors"
                    >
                      View Merchant Details →
                    </Link>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Color Legend Footer */}
          <div className="p-3 bg-[#031B38] border-t border-[#164B68] flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-[#A9BBCD] font-semibold text-[11px]">Legend:</span>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-[#FFA52B] border border-[#F08A00]" />
                <span className="text-white text-[11px]">Merchant</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-[#00B8C7] border border-[#00E0E0]" />
                <span className="text-white text-[11px]">Commitment</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-[#082746] border border-[#00E0E0]" />
                <span className="text-white text-[11px]">Transaction</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rotate-45 bg-[#F43F5E]" />
                <span className="text-white text-[11px]">Anomaly Insight</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-[#F4F7FB]" />
                <span className="text-white text-[11px]">User Account</span>
              </div>
            </div>

            <div className="text-[11px] text-[#A9BBCD]">
              Click any node to inspect attributes • Scroll or pinch to zoom • Drag canvas to pan
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
