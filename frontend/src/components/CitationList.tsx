/** Citation rendering component */
import { Citation } from '../types';
import './CitationList.css';

interface CitationListProps {
  citations: Citation[];
}

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) {
    return null;
  }

  return (
    <div className="citation-list">
      <h3>Citations</h3>
      <div className="citations">
        {citations.map((citation, index) => (
          <div key={index} className="citation-card">
            <div className="citation-header">
              <span className="citation-source">{citation.source}</span>
              <span className="citation-id">ID: {citation.chunk_id}</span>
            </div>
            {citation.quote && (
              <div className="citation-quote">"{citation.quote}"</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
