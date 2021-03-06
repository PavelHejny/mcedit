import atexit
import os
import shutil
import tempfile
import pymclevel
from mceutils import showProgress
from pymclevel.mclevelbase import exhaust

undo_folder = os.path.join(tempfile.gettempdir(), "mcedit_undo")
if not os.path.exists(undo_folder):
    os.mkdir(undo_folder)

def mkundotemp():
    return tempfile.mkdtemp("mceditundo", dir=undo_folder)

atexit.register(shutil.rmtree, undo_folder, True)

class Operation(object):
    changedLevel = True
    undoLevel = None

    def __init__(self, editor, level):
        self.editor = editor
        self.level = level

    def extractUndo(self, level, box):
        return self.extractUndoChunks(level, box.chunkPositions, box.chunkCount)

    def extractUndoChunks(self, level, chunks, chunkCount = None):
        undoLevel = pymclevel.MCInfdevOldLevel(mkundotemp(), create=True)
        if not chunkCount:
            try:
                chunkCount = len(chunks)
            except TypeError:
                chunkCount = -1

        def _extractUndo():
            yield 0, 0, "Recording undo..."
            for i, (cx, cz) in enumerate(chunks):
                undoLevel.copyChunkFrom(level, cx, cz)
                yield i, chunkCount, "Copying chunk %s..." % ((cx, cz),)
            undoLevel.saveInPlace()

        if chunkCount > 25 or chunkCount < 1:
            showProgress("Recording undo...", _extractUndo())
        else:
            exhaust(_extractUndo())

        return undoLevel

    # represents a single undoable operation
    def perform(self, recordUndo=True):
        " Perform the operation. Record undo information if recordUndo"

    def undo(self):
        """ Undo the operation. Ought to leave the Operation in a state where it can be performed again.
            Default implementation copies all chunks in undoLevel back into level. Non-chunk-based operations
            should override this."""

        if self.undoLevel:

            def _undo():
                yield 0, 0, "Undoing..."
                for i, (cx, cz) in enumerate(self.undoLevel.allChunks):
                    self.level.copyChunkFrom(self.undoLevel, cx, cz)
                    yield i, self.undoLevel.chunkCount, "Copying chunk %s..." % ((cx, cz),)

            if self.undoLevel.chunkCount > 25:
                showProgress("Undoing...", _undo())
            else:
                exhaust(_undo())

            self.editor.invalidateChunks(self.undoLevel.allChunks)


    def dirtyBox(self):
        """ The region modified by the operation.
        Return None to indicate no blocks were changed.
        """
        return None
