import curtsies
import time
import threading
import traceback
import sys


# TODO: reject tmux sessions - it does not seem to play nice
# TODO: return screen on pause_point
# TODO: keep a time counter after the line
# TODO: show context of line (ie lines around)

def managing_thread_main():
	import shutit_global
	def gather_module_paths():
		shutit_global_object = shutit_global.shutit_global_object
		owd = shutit_global_object.owd
		shutit_module_paths = set()
		for shutit_object in shutit_global.shutit_global_object.shutit_objects:
			shutit_module_paths = shutit_module_paths.union(set(shutit_object.host['shutit_module_path']))
		if '.' in shutit_module_paths:
			shutit_module_paths.remove('.')
			shutit_module_paths.add(owd)
		for path in shutit_module_paths:
			if path[0] != '/':
				shutit_module_paths.remove(path)
				shutit_module_paths.add(owd + '/' + path)
		return shutit_module_paths
	time.sleep(1)
	shutit_module_paths = gather_module_paths()
	shutit_global.shutit_global_object.stacktrace_lines_arr = ['CONTEXT',]
	while True:
		# Acquire lock to write screen. Prevents nasty race conditions.
		if shutit_global.shutit_global_object.global_thread_lock.acquire(False):
			# Go to sleep as spinning doesn't help anyone here.
			time.sleep(1)
			continue
		code = []
		for thread_id, stack in sys._current_frames().items():
			# ignore own thread:
			if thread_id == threading.current_thread().ident:
				continue
			for filename, lineno, name, line in traceback.extract_stack(stack):
				# if the file is in the same folder or subfolder as a folder in: self.host['shutit_module_path']
				# then show that context
				for shutit_module_path in shutit_module_paths:
					if filename.find(shutit_module_path) == 0:
						line = '===> ' + str(line.strip())
						if shutit_global.shutit_global_object.stacktrace_lines_arr[-1] != line:
							code.append('=> %s:%d:%s' % (filename, lineno, name))
							code.append('%s' % (line,))
		for line in code:
			shutit_global.shutit_global_object.stacktrace_lines_arr.append(line)
		shutit_global.shutit_global_object.pane_manager.draw_screen(draw_type='default')
		shutit_global.shutit_global_object.global_thread_lock.release()


def track_main_thread():
	t = threading.Thread(target=managing_thread_main)
	t.daemon = True
	t.start()