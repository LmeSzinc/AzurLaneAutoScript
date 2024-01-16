import './security-restrictions';
import {App} from './core/App';
import {logger} from '@/core/Logger/customLogger';

new App().bootstrap().catch(e => {
  logger.error(e);
});
