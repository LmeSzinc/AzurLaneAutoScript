import './security-restrictions';
import {App} from './core/App';
new App().bootstrap().catch(e => {
  console.error(e);
});
