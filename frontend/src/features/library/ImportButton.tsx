import { useNavigate } from 'react-router-dom';

import { ro } from '../../i18n/ro';
import { Button } from '../../ui/Button';
import { PlusIcon } from '../../ui/PlusIcon';
import { useAddFolderDialog } from './addFolderStore';

/** Butonul principal din bara de sus: duce în Bibliotecă și deschide „Adaugă folder”. */
export function ImportButton() {
  const navigate = useNavigate();
  const setOpen = useAddFolderDialog((s) => s.setOpen);
  return (
    <Button
      variant="primary"
      onClick={() => {
        navigate('/biblioteca');
        setOpen(true);
      }}
    >
      <PlusIcon />
      {ro.library.importButton}
    </Button>
  );
}
