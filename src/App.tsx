import { FaceWorkspace } from './FaceWorkspace';

export default function App() {
  return <div className="shell">
    <header><a href="#" className="wordmark">viel<span>✳</span></a><a href="#face-workspace">Open Face Cloak ↗</a></header>
    <main><section className="hero" aria-labelledby="headline"><span className="eyebrow">YOUR FACE. YOUR PRIVACY.</span><h1 id="headline">Keep the picture.<br/><span>Cloak your identity.</span></h1><p>Explore face cloaking against facial-recognition training, and test what it achieves on separate photos.</p><a className="primary" href="#face-workspace">Open the workspace ↓</a><div className="status"><span className="dot"/> Fawkes research integration · measured results, no automatic protection claim</div></section><FaceWorkspace /></main>
    <footer><span className="wordmark">viel</span><p>Fawkes integration by viel. No affiliation with or endorsement by SANDLab.</p></footer>
  </div>;
}
