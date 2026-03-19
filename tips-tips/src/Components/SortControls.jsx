import React from "react";

export default function SortControls({ sortBy, setSortBy }) {
  const isSortedByLikes = sortBy === "likes";

  return (
    <div className="sortControls">
      <button
        type="button"
        onClick={() => setSortBy(isSortedByLikes ? "" : "likes")}
      >
        {isSortedByLikes ? "人気順を解除" : "人気順で表示"}
      </button>
    </div>
  );
}
